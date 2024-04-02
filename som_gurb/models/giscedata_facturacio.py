from osv import osv


class GiscedataFacturacioServices(osv.osv):

    _inherit = "giscedata.facturacio.services"

    def _get_vals_linia(self, cursor, uid, service, inv, context=None):
        if context is None:
            context = {}

        gurb_cups_o = self.pool.get("som.gurb.cups")
        imd_o = self.pool.get("ir.model.data")
        product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_gurb"
        )[1]

        for vals in super(GiscedataFacturacioServices, self)._get_vals_linia(
            cursor, uid, service, inv, context=context
        ):
            if product_id == vals.get("product_id", False):
                for gurb_cups_id in self._get_gurb_cups_ids(
                    cursor, uid, inv, vals, context=context
                ):
                    gurb_cups_br = gurb_cups_o.browse(cursor, uid, gurb_cups_id)
                    vals["multi"] = vals["quantity"]
                    vals["quantity"] = gurb_cups_br.beta_kw
                    yield vals
            else:
                yield vals

    def _get_gurb_cups_ids(self, cursor, uid, inv, vals, context=None):
        if context is None:
            context = {}

        context["active_test"] = False
        gurb_cups_o = self.pool.get("som.gurb.cups")
        cups_id = inv.polissa_id.cups.id
        start_date = vals["data_desde"]
        end_date = vals["data_fins"]
        search_params = [
            ("cups_id", "=", cups_id),
            "|",
            ("start_date", "<=", end_date),
            ("end_date", ">=", start_date),
        ]

        gurb_cups_ids = gurb_cups_o.search(cursor, uid, search_params, context=context)
        return gurb_cups_ids


GiscedataFacturacioServices()
