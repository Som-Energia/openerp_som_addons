from osv import osv
from datetime import datetime


def _str_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


class GiscedataFacturacioServices(osv.osv):

    _inherit = "giscedata.facturacio.services"

    def _get_vals_linia(self, cursor, uid, service, inv, context=None):
        if context is None:
            context = {}

        context["dont_group_lines"] = True

        gurb_o = self.pool.get("som.gurb")
        gurb_cups_beta_o = self.pool.get("som.gurb.cups.beta")

        products_ids = gurb_o.get_gurb_products_ids(cursor, uid, context=context)

        for vals in super(GiscedataFacturacioServices, self)._get_vals_linia(
            cursor, uid, service, inv, context=context
        ):
            product_id = vals.get("product_id", False)
            if (
                product_id in products_ids
            ):
                line_start_date = _str_to_date(vals["data_desde"])
                line_end_date = _str_to_date(vals["data_fins"])
                for gurb_cups_beta_id in self._get_gurb_cups_betas_ids(
                    cursor, uid, inv, vals, context=context
                ):
                    res_vals = vals.copy()
                    gurb_cups_beta_br = gurb_cups_beta_o.browse(cursor, uid, gurb_cups_beta_id)

                    gurb_cups_start_date = _str_to_date(gurb_cups_beta_br.start_date)
                    if gurb_cups_beta_br.end_date:
                        gurb_cups_end_date = _str_to_date(gurb_cups_beta_br.end_date)
                    else:
                        gurb_cups_end_date = False

                    line_start_date = _str_to_date(vals["data_desde"])
                    line_end_date = _str_to_date(vals["data_fins"])

                    if not gurb_cups_end_date:
                        end_date = line_end_date
                    else:
                        end_date = min(line_end_date, gurb_cups_end_date)
                    start_date = max(line_start_date, gurb_cups_start_date)

                    days = (end_date - start_date).days + 1

                    res_vals["data_desde"] = datetime.strftime(start_date, "%Y-%m-%d")
                    res_vals["data_fins"] = datetime.strftime(end_date, "%Y-%m-%d")
                    res_vals["quantity"] = gurb_cups_beta_br.beta_kw
                    res_vals["multi"] = days if days > 0 else 0

                    yield res_vals

                    if gurb_cups_beta_br.gift_beta_kw > 0:
                        gift_values = res_vals.copy()
                        gift_values["multi"] = 0
                        gift_values["quantity"] = gurb_cups_beta_br.gift_beta_kw
                        gift_values["name"] = "{} {}".format(gift_values["name"], " (beta regal)")
                        yield gift_values
            else:
                yield vals

    def _get_gurb_cups_betas_ids(self, cursor, uid, inv, vals, context=None):
        if context is None:
            context = {}
        context["active_test"] = False

        gurb_cups_o = self.pool.get("som.gurb.cups")
        gurb_cups_beta_o = self.pool.get("som.gurb.cups.beta")

        search_params = [
            ("cups_id", "=", inv.polissa_id.cups.id),
            ("start_date", "<=", vals["data_fins"]),
            ("end_date", "=", False),
        ]
        gurb_cups_ids = gurb_cups_o.search(cursor, uid, search_params, context=context)

        search_params = [
            ("cups_id", "=", inv.polissa_id.cups.id),
            ("start_date", "<=", vals["data_fins"]),
            ("end_date", ">=", vals["data_desde"]),
        ]
        gurb_cups_ids += gurb_cups_o.search(cursor, uid, search_params, context=context)

        if not gurb_cups_ids:
            return []

        search_params = [
            ("gurb_cups_id", "=", gurb_cups_ids[0]),
            ("start_date", "<=", vals["data_fins"]),
            ("end_date", "=", False),
            ("future_beta", "=", False),
        ]
        gurb_cups_beta_ids = gurb_cups_beta_o.search(cursor, uid, search_params, context=context)

        search_params = [
            ("gurb_cups_id", "=", gurb_cups_ids[0]),
            ("start_date", "<=", vals["data_fins"]),
            ("end_date", ">=", vals["data_desde"]),
            ("future_beta", "=", False),
        ]
        gurb_cups_beta_ids += gurb_cups_beta_o.search(cursor, uid, search_params, context=context)

        return gurb_cups_beta_ids


GiscedataFacturacioServices()
