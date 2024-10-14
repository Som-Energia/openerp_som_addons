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


EXECUTION_STATES = [
    ("pending", _(u"Pendent")),
    ("doing", _(u"Executant-se")),
    ("equals", _(u"Iguals")),
    ("differents", _(u"Amb diferències")),
    ("pdf_error", _(u"Error en generar")),
    ("no_expected", _(u"Sense doc. original")),
    ("error", _(u"Error desconegut")),
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

    def execute_one_test(self, cursor, uid, id, context=None):
        self._set_status(cursor, uid, id, 'pending')
        self._set_status(cursor, uid, id, 'doing')
        result_ok, result_pdf = self._generate_pdf(cursor, uid, id, context)

        if result_ok is not True:
            self._set_status(cursor, uid, id, 'pdf_error', result_pdf)
            return _("Error generant pdf")

        expected_pdf = self._get_extected_attachment(cursor, uid, id, context)
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
            return _("Error sense fitxer generat")

        self._store_expected_attachment(cursor, uid, id, data, context=context)
        self._del_result_attachment(cursor, uid, id, context=context)
        return _("Fitxer acceptat")

    def _set_status(self, cursor, uid, ids, status, log=''):
        self.write(cursor, uid, ids, {
            'result': status,
            'result_log': log,
        })

    def _store_file(self, cursor, uid, content, file_name, test_id, context=None):
        b64_content = base64.b64encode(content)

        att_obj = self.pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('name', '=', file_name),
            ('res_model', '=', 'report.test'),
            ('res_id', '=', test_id),
        ])

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

        att_obj = self.pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('name', '=', file_name),
            ('res_model', '=', 'report.test'),
            ('res_id', '=', test_id),
        ])

        if not att_ids:
            return None

        att_id = att_ids[0]
        b64_content = att_obj.read(cursor, uid, att_id, ["datas"])["datas"]
        content = base64.b64decode(b64_content)
        return content

    def _del_file(self, cursor, uid, file_name, test_id, context=None):
        att_obj = self.pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('name', '=', file_name),
            ('res_model', '=', 'report.test'),
            ('res_id', '=', test_id),
        ])

        if not att_ids:
            return None

        att_id = att_ids[0]
        att_obj.unlink(cursor, uid, att_id, context=context)
        return True

    def _store_result_attachment(self, cursor, uid, id, data, context=None):
        return self._store_file(cursor, uid, data, "result.pdf", id, context=context)

    def _store_diff_attachment(self, cursor, uid, id, data, context=None):
        return self._store_file(cursor, uid, data, "diff.pdf", id, context=context)

    def _store_expected_attachment(self, cursor, uid, id, data, context=None):
        return self._store_file(cursor, uid, data, "expected.pdf", id, context=context)

    def _get_result_attachment(self, cursor, uid, id, context=None):
        return self._read_file(cursor, uid, "result.pdf", id, context=context)

    def _get_extected_attachment(self, cursor, uid, id, context=None):
        return self._read_file(cursor, uid, "expected.pdf", id, context=context)

    def _del_result_attachment(self, cursor, uid, id, context=None):
        return self._del_file(cursor, uid, "result.pdf", id, context=context)

    def _generate_pdf(self, cursor, uid, id, context=None):
        data = self.browse(cursor, uid, id)
        report_name = "report." + data.report.report_name
        res_ids = [data.res_id]
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
        "res_id": fields.integer(
            _("Id"),
            help=_("Id del registre a testejar"),
            required=True
        ),
    }

    _defaults = {
        "active": lambda *a: True,
        "result_log": lambda *a: '',
    }


ReportTest()
