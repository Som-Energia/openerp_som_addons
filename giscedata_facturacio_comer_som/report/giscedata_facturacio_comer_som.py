# -*- coding: utf-8 -*-

from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import pooler
from datetime import datetime
import base64


class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        super(report_webkit_html, self).__init__(cursor, uid, name, context=context)
        self.localcontext.update(
            {
                "cursor": cursor,
                "uid": uid,
                "addons_path": config["addons_path"],
            }
        )


class FacturaReportSomWebkitParserHTML(webkit_report.WebKitParser):
    def __init__(
        self,
        name="report.giscedata.facturacio.factura",
        table="giscedata.facturacio.factura",
        rml=None,
        parser=report_webkit_html,
        header=True,
        store=False,
    ):

        super(FacturaReportSomWebkitParserHTML, self).__init__(
            name, table, rml, parser, header, store
        )

    def _get_filename(self, fact_number):
        return 'STORED_{}.pdf'.format(fact_number)

    def _search_stored(self, cursor, uid, ids, data, context=None):
        if len(ids) != 1:
            return False, ''

        if context is None:
            context = {}

        if context.get("no_store", False):
            return False, ''

        fact_id = ids[0]
        pool = pooler.get_pool(cursor.dbname)
        fact_obj = pool.get("giscedata.facturacio.factura")
        fact_number = fact_obj.read(cursor, uid, fact_id, ['number'])['number']
        if not fact_number:
            return False, ''

        filename = self._get_filename(fact_number)
        att_ids = self._exists_file(cursor, uid, filename, fact_id, context=context)
        if att_ids:
            return True, self._recover_file(cursor, uid, att_ids[0], context=context)

        old_ids = self._exists_mailbox_file(cursor, uid, fact_number, context=context)
        if old_ids:
            return True, self._recover_file(cursor, uid, old_ids[0], context=context)

        return False, ''

    def _store(self, cursor, uid, ids, res, context=None):
        if len(ids) != 1:
            return False

        if context is None:
            context = {}

        if context.get("no_store", False):
            return False

        fact_id = ids[0]
        pool = pooler.get_pool(cursor.dbname)
        fact_obj = pool.get("giscedata.facturacio.factura")
        fact_number = fact_obj.read(cursor, uid, fact_id, ['number'])['number']
        # TODO discard documents
        if not fact_number:
            return False

        file_name = self._get_filename(fact_number)
        att_ids = self._exists_file(cursor, uid, file_name, fact_id, context=context)
        if not att_ids:
            self._store_file(cursor, uid, res[0], file_name, fact_id, context=context)
        return True

    def _exists_mailbox_file(self, cursor, uid, fact_number, context=None):
        pool = pooler.get_pool(cursor.dbname)
        att_obj = pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('name', 'like', '%{}%'.format(fact_number)),
            ('res_model', '=', 'poweremail.mailbox'),
            ('datas_fname', '=', '{}.pdf'.format(fact_number)),
            ('link', '=', None),
        ], context=context)
        return att_ids

    def _exists_file(self, cursor, uid, file_name, fact_id, context=None):
        pool = pooler.get_pool(cursor.dbname)
        att_obj = pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('name', '=', file_name),
            ('res_model', '=', 'giscedata.facturacio.factura'),
            ('res_id', '=', fact_id),
        ], context=context)
        return att_ids

    def _store_file(self, cursor, uid, content, file_name, fact_id, context=None):
        pool = pooler.get_pool(cursor.dbname)
        att_obj = pool.get("ir.attachment")
        b64_content = base64.b64encode(content)
        attachment = {
            "name": file_name,
            "datas": b64_content,
            "datas_fname": file_name,
            "res_model": "giscedata.facturacio.factura",
            "res_id": fact_id,
        }
        with pooler.get_db(cursor.dbname).cursor() as w_cursor:
            attachment_id = att_obj.create(
                w_cursor, uid, attachment, context=context
            )
        return attachment_id

    def _recover_file(self, cursor, uid, att_id, context=None):
        pool = pooler.get_pool(cursor.dbname)
        att_obj = pool.get("ir.attachment")
        b64_content = att_obj.read(cursor, uid, att_id, ["datas"])["datas"]
        content = base64.b64decode(b64_content)
        return [content, u'pdf']

    def create(self, cursor, uid, ids, data, context=None):
        """
        To sign PDF of certain factures
        :param cursor:
        :param uid:
        :param ids:
        :param data:
        :param context:
        :return:
        """

        ok, res = self._search_stored(cursor, uid, ids, data, context=context)
        if ok:
            return res

        if context is None:
            context = {}
        pool = pooler.get_pool(cursor.dbname)
        factura_o = pool.get("giscedata.facturacio.factura")
        polissa_o = pool.get("giscedata.polissa")
        partner_o = pool.get("res.partner")
        imd_o = pool.get("ir.model.data")

        sign_rp_id = imd_o.get_object_reference(
            cursor, uid, "giscedata_facturacio_comer_som", "cat_rp_factura_sign"
        )[1]
        sign_gp_id = imd_o.get_object_reference(
            cursor, uid, "giscedata_facturacio_comer_som", "cat_gp_factura_sign"
        )[1]
        have_to_sign = False
        fact_info = factura_o.read(cursor, uid, ids, ["polissa_id", "partner_id"])
        partner_ids = [x["partner_id"][0] for x in fact_info]
        partner_category_info = partner_o.read(cursor, uid, partner_ids, ["category_id"])
        partner_category_ids = set()
        for x in partner_category_info:
            partner_category_ids.update(x["category_id"])
        have_to_sign = sign_rp_id in partner_category_ids
        if not have_to_sign:
            polissa_ids = [x["polissa_id"][0] for x in fact_info]
            polissa_category_info = polissa_o.read(cursor, uid, polissa_ids, ["category_id"])
            polissa_category_ids = set()
            for x in polissa_category_info:
                polissa_category_ids.update(x["category_id"])

            have_to_sign = sign_gp_id in polissa_category_ids

        if have_to_sign:
            ctx = context.copy()
            ctx["webkit_signed_pdf"] = True
            ctx["extra_commands"] = [
                "-V",
                '--l2-text "Firma digital a {}"'.format(datetime.today().strftime("%d/%m/%Y")),
                "-llx 320",
                "-lly 1030",
            ]
            res = super(FacturaReportSomWebkitParserHTML, self).create(
                cursor, uid, ids, data, context=ctx
            )
        else:
            res = super(FacturaReportSomWebkitParserHTML, self).create(
                cursor, uid, ids, data, context=context
            )
        self._store(cursor, uid, ids, res, context=context)
        return res


FacturaReportSomWebkitParserHTML(
    "report.giscedata.facturacio.factura",
    "giscedata.facturacio.factura",
    "giscedata_facturacio_comer_som/report/report_giscedata_facturacio_factura_comer.mako",
    parser=report_webkit_html,
)
