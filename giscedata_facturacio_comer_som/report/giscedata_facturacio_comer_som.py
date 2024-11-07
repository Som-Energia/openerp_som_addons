# -*- coding: utf-8 -*-

from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import pooler
from datetime import datetime
from ..invoice_pdf_storer import InvoicePdfStorer


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

    def create(self, cursor, uid, ids, data, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        storer = InvoicePdfStorer(cursor, uid, context)
        for f_id in ids:
            if not storer.search_stored_and_append(f_id):
                res = self.sub_create(cursor, uid, [f_id], data, context=context)
                storer.append_and_store(f_id, res)

        return storer.retrieve()

    def sub_create(self, cursor, uid, ids, data, context=None):
        """
        To sign PDF of certain factures
        :param cursor:
        :param uid:
        :param ids:
        :param data:
        :param context:
        :return:
        """

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
        return res


FacturaReportSomWebkitParserHTML(
    "report.giscedata.facturacio.factura",
    "giscedata.facturacio.factura",
    "giscedata_facturacio_comer_som/report/report_giscedata_facturacio_factura_comer.mako",
    parser=report_webkit_html,
)
