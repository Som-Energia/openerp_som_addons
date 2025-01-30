# -*- coding: utf-8 -*-
from osv import osv
from report_backend.report_backend import report_browsify


class GiscedataFacturacioFacturaReportV2(osv.osv):
    _inherit = "giscedata.facturacio.factura.report.v2"

    def get_parametres_energia(self, data):
        parametres_energia = super(GiscedataFacturacioFacturaReportV2, self).get_parametres_energia(
            data
        )
        parametres_energia_sense_gwkh = []
        for parametre in parametres_energia:
            if parametre[0] != "prEh":
                parametres_energia_sense_gwkh.append(parametre)
        return parametres_energia_sense_gwkh

    def get_tc(self, data):
        tc = super(GiscedataFacturacioFacturaReportV2, self).get_tc(data)

        if data["factura"]["te_gkwh"]:
            tc = "I0"

        return tc

    @report_browsify
    def get_factura(self, cursor, uid, fra, context=None):
        res = super(GiscedataFacturacioFacturaReportV2, self).get_factura(
            cursor, uid, fra, context=context
        )
        res["te_gkwh"] = fra.is_gkwh

        donatiu = self._get_donatiu_amount(cursor, uid, fra, context=context)
        fraccio = self._get_fraccionament_amount(cursor, uid, fra, context=context)
        res["total_linies_impostos"] = res["import"] - donatiu - fraccio
        res["te_iva_21"] = self._get_te_iva_21(cursor, uid, fra, context=context)
        return res

    def _get_donatiu_amount(self, cursor, uid, fra, context=None):
        donatiu_lines = [
            l.price_subtotal
            for l in fra.linia_ids  # noqa: E741
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "DN01"
        ]

        return sum(donatiu_lines)

    def _get_fraccionament_amount(self, cursor, uid, fra, context=None):
        model_obj = self.pool.get("ir.model.data")
        fraccio_prod_id = model_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "default_fraccionament_product"
        )[1]

        faccionament_lines = [
            l.price_subtotal
            for l in fra.linia_ids  # noqa: E741
            if l.invoice_line_id.product_id.id == fraccio_prod_id
        ]
        return sum(faccionament_lines)

    def _get_te_iva_21(self, cursor, uid, fra, context=None):
        cfg_obj = self.pool.get('res.config')
        list_conf_ids = []
        try:
            list_conf_ids = eval(cfg_obj.get(cursor, uid, "som_tax_21_ids_for_invoice_mail", "[]"))
        except Exception:
            pass
        if len(fra.tax_line) > 0:
            list_fra_tax_ids = fra.tax_line.tax_id.id
        else:
            list_fra_tax_ids = []
        common_elements = [id for id in list_fra_tax_ids if id in list_conf_ids]
        return len(common_elements) > 0

    def _get_linies_totals(self, cursor, uid, fra, context=None):
        res = super(GiscedataFacturacioFacturaReportV2, self)._get_linies_totals(
            cursor, uid, fra, context=context
        )

        res["donatiu"] = {
            "import": self._get_donatiu_amount(cursor, uid, fra, context=context),
        }
        res["fraccionament"] = {
            "import": self._get_fraccionament_amount(cursor, uid, fra, context=context),
        }
        return res

    def get_impsa(self, data, linies_importe_otros):
        res = super(GiscedataFacturacioFacturaReportV2, self).get_impsa(data, linies_importe_otros)
        for linia in data["linies"]["donatiu"]:
            if linia["metadata"]["code"] in ["DN01", "DN02", "DONATIU"]:
                donatiu_sense_iva = linia["import"].val / 1.21
                res += float(format(donatiu_sense_iva, ".2f"))
        return res

    # Posem total_preu_linies_sense_iva perquè els conceptes de linia sense iva estan a impsa / 1.21
    # Ens ho ha comunicat la CNMC que s'ha de fer així
    def get_linies_importe_otros(self, data):
        linies_importe_otros, total_preu_linies_sense_iva = super(
            GiscedataFacturacioFacturaReportV2, self
        ).get_linies_importe_otros(data)
        return linies_importe_otros, 0

    def get_verde(self, data):
        return 1

    @report_browsify
    def get_linies(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        res = super(GiscedataFacturacioFacturaReportV2, self).get_linies(
            cursor, uid, fra, context=context
        )

        model_obj = self.pool.get("ir.model.data")

        # Treure les linees de donatiu i fraccionament d'altres i posar-les al seu tag corresponent
        res["donatiu"] = []
        res["fraccionament"] = []

        fraccio_prod_id = model_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "default_fraccionament_product"
        )[1]

        for where in ["altres", "cobrament"]:
            if where in res.keys():
                to_pop = []
                for index, linia in enumerate(res[where]):
                    if linia["metadata"] and linia["metadata"].get("code") in [
                        "DN01",
                        "DN02",
                        "DONATIU",
                    ]:
                        res["donatiu"].append(linia)
                        to_pop.append(index)
                    if linia["metadata"] and linia["metadata"].get("product_id") == fraccio_prod_id:
                        res["fraccionament"].append(linia)
                        to_pop.append(index)

                for idx in reversed(to_pop):
                    res[where].pop(idx)

        return res


GiscedataFacturacioFacturaReportV2()
