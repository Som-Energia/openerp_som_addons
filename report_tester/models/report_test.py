# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import netsvc
import traceback
import base64
import tempfile
import shutil
import os
import subprocess
from oorq.decorators import job


EXECUTION_STATES = [
    ("pending", _(u"Pendent")),
    ("doing", _(u"Executant-se")),
    ("equals", _(u"Iguals")),
    ("differents", _(u"Amb diferències")),
    ("pdf_error", _(u"Error en generar")),
    ("no_expected", _(u"Sense doc. original")),
    ("error", _(u"Error desconegut")),
]


RES_INTERPRETER = [
    ("id", _(u"Id")),
    ("fact_pol", _(u"Última factura de la pòlissa")),
    ("id_pol", _(u"Id de la pòlissa")),
    ("id_fact", _(u"Id de la factura")),
]


class ReportTest(osv.osv):

    _name = "report.test"
    _order = "priority"

    def execute_test(self, cursor, uid, test_ids, context=None):
        if context is None:
            context = {}

        result = ""
        fields = ['priority', 'active', 'name']
        tests_data = self.read(cursor, uid, test_ids, fields)
        for test_data in sorted(tests_data, key=lambda e: e['priority']):
            if test_data['active']:
                one_result = self.execute_one_test(cursor, uid, test_data['id'], context)
                result += _(" - Executant test '{}' --> {} \n".format(
                    test_data['name'],
                    one_result
                ))
            else:
                result += _(" - Executant test '{}' --> no actiu!! \n".format(
                    test_data['name']
                ))

        return result

    @job(queue='reports', timeout=3600)
    def execute_one_test_async(self, cursor, uid, id, context=None):
        self.execute_one_test(cursor, uid, id, context=context)
        return True

    def execute_one_test(self, cursor, uid, id, context=None):
        self._set_status(cursor, uid, id, 'pending')
        self._del_result_attachment(cursor, uid, id, context=context)
        self._del_diff_attachment(cursor, uid, id, context=context)
        self._set_status(cursor, uid, id, 'doing')
        result_ok, result_pdf = self._generate_pdf(cursor, uid, id, context)

        if result_ok is not True:
            self._set_status(cursor, uid, id, 'pdf_error', result_pdf)
            return _("Error generant pdf")

        expected_pdf = self._get_expected_attachment(cursor, uid, id, context)
        if not expected_pdf:
            self._set_status(cursor, uid, id, 'no_expected')
            self._store_result_attachment(cursor, uid, id, result_pdf, context)
            return _("Sense original per comprovar")

        equals, diff_pdf = self._compare_pdf(cursor, uid, result_pdf, expected_pdf)
        if equals:
            self._set_status(cursor, uid, id, 'equals')
            return _("Identics, sense canvis")
        else:
            self._set_status(cursor, uid, id, 'differents')
            self._store_result_attachment(cursor, uid, id, result_pdf, context)
            self._store_diff_attachment(cursor, uid, id, diff_pdf, context)
            return _("Diferències trobades")

        self._set_status(cursor, uid, id, 'error')
        return _("Error indeterminat")

    def accept_test(self, cursor, uid, test_ids, context=None):
        if context is None:
            context = {}

        result = ""
        fields = ['priority', 'active', 'name']
        tests_data = self.read(cursor, uid, test_ids, fields)
        for test_data in sorted(tests_data, key=lambda e: e['priority']):
            if test_data['active']:
                one_result = self.accept_one_test(cursor, uid, test_data['id'], context)
                result += _(" - Acceptant test '{}' --> {} \n".format(
                    test_data['name'],
                    one_result
                ))
            else:
                result += _(" - Acceptant test '{}' --> no actiu!! \n".format(
                    test_data['name']
                ))

        return result

    def accept_one_test(self, cursor, uid, id, context=None):

        data = self._get_result_attachment(cursor, uid, id, context=context)
        if not data:
            if self._exists_expected_attachment(cursor, uid, id, context=context):
                return _("Res per acceptar / Ja acceptat")
            else:
                return _("Error sense fitxers!")

        self._store_expected_attachment(cursor, uid, id, data, context=context)
        self._del_result_attachment(cursor, uid, id, context=context)
        self._del_diff_attachment(cursor, uid, id, context=context)
        self._set_status(cursor, uid, id, 'equals')
        return _("Fitxer acceptat")

    def _set_status(self, cursor, uid, ids, status, log=''):
        self.write(cursor, uid, ids, {
            'result': status,
            'result_log': log,
        })

    def _exists_file(self, cursor, uid, file_name, test_id, context=None):

        att_obj = self.pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('name', '=', file_name),
            ('res_model', '=', 'report.test'),
            ('res_id', '=', test_id),
        ])
        return att_ids

    def _store_file(self, cursor, uid, content, file_name, test_id, context=None):
        att_obj = self.pool.get("ir.attachment")
        b64_content = base64.b64encode(content)
        att_ids = self._exists_file(cursor, uid, file_name, test_id, context=context)
        if att_ids:
            att_id = att_ids[0]

            att_obj.write(cursor, uid, att_id, {
                "datas": b64_content,
            })
            return att_id
        else:
            attachment = {
                "name": file_name,
                "datas": b64_content,
                "datas_fname": file_name,
                "res_model": "report.test",
                "res_id": test_id,
            }
            attachment_id = att_obj.create(
                cursor, uid, attachment, context=context
            )
            return attachment_id

    def _read_file(self, cursor, uid, file_name, test_id, context=None):
        att_ids = self._exists_file(cursor, uid, file_name, test_id, context=context)
        if not att_ids:
            return None

        att_id = att_ids[0]
        att_obj = self.pool.get("ir.attachment")
        b64_content = att_obj.read(cursor, uid, att_id, ["datas"])["datas"]
        content = base64.b64decode(b64_content)
        return content

    def _del_file(self, cursor, uid, file_name, test_id, context=None):
        att_ids = self._exists_file(cursor, uid, file_name, test_id, context=context)
        if not att_ids:
            return None

        att_id = att_ids[0]
        att_obj = self.pool.get("ir.attachment")
        att_obj.unlink(cursor, uid, att_id, context=context)
        return True

    def _get_attachment_file_expected(self, cursor, uid, id, context=None):
        return "expected.pdf"

    def _get_attachment_file_result(self, cursor, uid, id, context=None):
        return "result.pdf"

    def _get_attachment_file_diff(self, cursor, uid, id, context=None):
        return "diff.pdf"

    def _store_result_attachment(self, cursor, uid, id, data, context=None):
        result = self._get_attachment_file_result(cursor, uid, id, context=context)
        return self._store_file(cursor, uid, data, result, id, context=context)

    def _store_diff_attachment(self, cursor, uid, id, data, context=None):
        diff = self._get_attachment_file_diff(cursor, uid, id, context=context)
        return self._store_file(cursor, uid, data, diff, id, context=context)

    def _store_expected_attachment(self, cursor, uid, id, data, context=None):
        expected = self._get_attachment_file_expected(cursor, uid, id, context=context)
        return self._store_file(cursor, uid, data, expected, id, context=context)

    def _get_result_attachment(self, cursor, uid, id, context=None):
        result = self._get_attachment_file_result(cursor, uid, id, context=context)
        return self._read_file(cursor, uid, result, id, context=context)

    def _get_diff_attachment(self, cursor, uid, id, context=None):
        diff = self._get_attachment_file_diff(cursor, uid, id, context=context)
        return self._read_file(cursor, uid, diff, id, context=context)

    def _get_expected_attachment(self, cursor, uid, id, context=None):
        expected = self._get_attachment_file_expected(cursor, uid, id, context=context)
        return self._read_file(cursor, uid, expected, id, context=context)

    def _exists_expected_attachment(self, cursor, uid, id, context=None):
        expected = self._get_attachment_file_expected(cursor, uid, id, context=context)
        return self._exists_file(cursor, uid, expected, id, context=context)

    def _del_result_attachment(self, cursor, uid, id, context=None):
        result = self._get_attachment_file_result(cursor, uid, id, context=context)
        return self._del_file(cursor, uid, result, id, context=context)

    def _del_diff_attachment(self, cursor, uid, id, context=None):
        diff = self._get_attachment_file_diff(cursor, uid, id, context=context)
        return self._del_file(cursor, uid, diff, id, context=context)

    def _get_resource_id(self, cursor, uid, id, context=None):
        data = self.read(cursor, uid, id, ['interpreter', 'value'])

        if data['interpreter'] == 'id':
            return int(data['value']), _("")

        if data['interpreter'] == 'fact_pol':
            pol_obj = self.pool.get("giscedata.polissa")
            pol_ids = pol_obj.search(cursor, uid, [
                ('name', '=', data['value']),
            ], context={"active_test": False})
            if not pol_ids:
                return False, _("Polissa >{}< no trobada").format(data['value'])

            fact_obj = self.pool.get("giscedata.facturacio.factura")
            fact_ids = fact_obj.search(cursor, uid,
                                       [
                                           ('polissa_id', '=', pol_ids[0]),
                                           ('type', 'in', ['out_invoice', 'out_refund']),
                                       ],
                                       order='data_final DESC',
                                       limit=1
                                       )
            if not fact_ids:
                return False, _("Polissa >{}< no té factures").format(data['value'])
            return fact_ids[0], _("")

        if data['interpreter'] == 'id_pol':
            pol_obj = self.pool.get("giscedata.polissa")
            pol_ids = pol_obj.search(cursor, uid, [
                ('name', '=', data['value']),
            ], context={"active_test": False})
            if not pol_ids:
                return False, _("Polissa >{}< no trobada").format(data['value'])
            return pol_ids[0], _("")

        if data['interpreter'] == 'id_fact':
            fact_obj = self.pool.get("giscedata.facturacio.factura")
            fact_ids = fact_obj.search(cursor, uid, [
                ('number', '=', data['value']),
            ])
            if not fact_ids:
                return False, _("Factura >{}< no trobada").format(data['value'])
            return fact_ids[0], _("")

        return False, _("Camp 'Valor es' no conegut!")

    def _generate_pdf(self, cursor, uid, id, context=None):
        data = self.browse(cursor, uid, id)
        report_name = "report." + data.report.report_name
        res_id, message = self._get_resource_id(cursor, uid, id, context=context)
        if not res_id:
            return False, message

        res_ids = [res_id]
        values = {
            "model": data.report.model,
            "id": res_ids,
            "report_type": "pdf",
        }
        try:
            report = netsvc.service_exist(report_name)
            result = report.create(cursor, uid, res_ids, values, context)
            return True, result[0]
        except Exception:
            tb = traceback.format_exc()
            return False, tb

    def _compare_pdf(self, cursor, uid, result, expected):
        tmp_dir = tempfile.mkdtemp(prefix='report-tester-')

        expected_pdf_path = os.path.join(tmp_dir, "expected.pdf")
        with open(expected_pdf_path, "wb") as f:
            f.write(expected)

        result_pdf_path = os.path.join(tmp_dir, "result.pdf")
        with open(result_pdf_path, "wb") as f:
            f.write(result)

        diff_pdf_path = os.path.join(tmp_dir, "diff.pdf")

        mdl_path = os.path.dirname(os.path.realpath(__file__))
        cmp_path = os.path.join(mdl_path, "../scripts/pdfcmp.sh")
        exit_code = subprocess.call([
            cmp_path,
            expected_pdf_path,
            result_pdf_path,
            diff_pdf_path
        ])
        if exit_code == 0:  # identical
            shutil.rmtree(tmp_dir)
            return True, ""
        else:
            with open(diff_pdf_path, "rb") as f:
                diff_pdf = f.read()
            shutil.rmtree(tmp_dir)
            return False, diff_pdf

    _columns = {
        "name": fields.char(
            _("Name"),
            size=64,
            required=True
        ),
        "description": fields.text(
            _("Descripció"),
            help=_(u"Descripció del que es vol testejar amb aquest test")
        ),
        "priority": fields.integer(
            _("Order"),
            required=True
        ),
        "active": fields.boolean(
            string=_(u"Actiu"),
            help=_(u"Indica si el test s'ha d'executar o no")
        ),
        "group_id": fields.many2one(
            "report.test.group",
            _(u"Grup de tests"),
            required=True
        ),
        "result": fields.selection(
            EXECUTION_STATES,
            _(u"Resultat"),
            help=_("Resultat de la darrera execució"),
            readonly=True
        ),
        "result_log": fields.text(
            _("log"),
            help=_(u"Resultat de l'execució del test"),
            readonly=True
        ),
        "report": fields.many2one(
            "ir.actions.report.xml",
            _(u"Report"),
            required=True
        ),
        "interpreter": fields.selection(
            RES_INTERPRETER,
            _(u"Valor es"),
            help=_("El camp Valor s'ha d'interpretar com"),
            required=True
        ),
        "value": fields.char(
            _("Valor"),
            size=64,
            help=_("Valor a ser interpretat per aconseguir el id del registre a testejar"),
            required=True
        ),
    }

    _defaults = {
        "active": lambda *a: True,
        "result_log": lambda *a: '',
    }


ReportTest()
