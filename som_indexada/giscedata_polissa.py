# -*- coding: utf-8 -*-
from osv import osv
from som_polissa.exceptions import exceptions
from som_indexada.utils import calculate_new_indexed_prices as calculate_new_indexed_prices_util


_TARIFA_CODIS_INDEXADA = {
    "2.0TD": {
        "peninsula": "pricelist_indexada_20td_peninsula_2024",
        "canaries": "pricelist_indexada_20td_canaries_2024",
        "balears": "pricelist_indexada_20td_balears_2024",
    },
    "3.0TD": {
        "peninsula": "pricelist_indexada_30td_peninsula_2024",
        "canaries": "pricelist_indexada_30td_canaries_2024",
        "balears": "pricelist_indexada_30td_balears_2024",
    },
    "6.1TD": {
        "peninsula": "pricelist_indexada_61td_peninsula_2024",
        "canaries": "pricelist_indexada_61td_canaries_2024",
        "balears": "pricelist_indexada_61td_balears_2024",
    },
}

_TARIFA_CODIS_PERIODES = {
    "2.0TD": {
        "peninsula": "pricelist_periodes_20td_peninsula",  # id 101
        "canaries": "pricelist_periodes_20td_insular",  # id 120
        "balears": "pricelist_periodes_20td_insular",
    },
    "3.0TD": {
        "peninsula": "pricelist_periodes_30td_peninsula",  # id 102
        "canaries": "pricelist_periodes_30td_insular",  # id 121
        "balears": "pricelist_periodes_30td_insular",
    },
    "6.1TD": {
        "peninsula": "pricelist_periodes_61td_peninsula",  # id 103
        "canaries": "pricelist_periodes_61td_insular",  # id 122
        "balears": "pricelist_periodes_61td_insular",
    },
}


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def get_pricelist_from_tariff_and_location(
            self, cursor, uid, access_tariff, mode_facturacio, id_municipi, context=None):
        IrModel = self.pool.get("ir.model.data")
        Pricelist = self.pool.get("product.pricelist")

        # Choose price list dict
        dict_pricelist_codis = _TARIFA_CODIS_PERIODES
        if mode_facturacio == "index":
            dict_pricelist_codis = _TARIFA_CODIS_INDEXADA

        if access_tariff not in dict_pricelist_codis:
            raise exceptions.TariffCodeNotSupported(access_tariff)

        location = self._get_tariff_zone_from_location(cursor, uid, id_municipi)

        search_params = [
            ("module", "=", "som_indexada"),
            ("name", "=", dict_pricelist_codis[access_tariff][location]),
        ]

        ir_model_id = IrModel.search(cursor, uid, search_params, context=context)[0]

        new_pricelist_id = IrModel.read(cursor, uid, ir_model_id, ["res_id"], context=context)[
            "res_id"
        ]

        new_pricelist_browse = Pricelist.browse(cursor, uid, new_pricelist_id, context=context)

        return new_pricelist_browse

    def _get_tariff_zone_from_location(self, cursor, uid, id_municipi):
        res_municipi_o = self.pool.get("res.municipi")
        municipi = res_municipi_o.browse(cursor, uid, id_municipi)
        subsistema_code = municipi.subsistema_id.code
        if subsistema_code in ['TF', 'PA', 'LG', 'HI', 'GC', 'FL']:
            return "canaries"
        elif subsistema_code in ['IF', 'MM']:
            return "balears"
        else:
            return "peninsula"

    def is_standard_price_list(self, cursor, uid, price_list_id, context=None):
        IrModel = self.pool.get("ir.model.data")

        for price_list_mode in (
            _TARIFA_CODIS_PERIODES,
            _TARIFA_CODIS_INDEXADA,
        ):
            for tarifa_codi, locations in price_list_mode.items():
                for location, semantic_id in locations.items():
                    # TODO: Could this resolution be calculated once?
                    standard_price_list_id = IrModel._get_obj(
                        cursor,
                        uid,
                        "som_indexada",
                        semantic_id,
                    )
                    if price_list_id == standard_price_list_id.id:
                        return True
        return False

    def calculate_new_indexed_prices(self, cursor, uid, id, context=None):
        pol = self.browse(cursor, uid, id)
        return calculate_new_indexed_prices_util(cursor, uid, pol, context=context)


GiscedataPolissa()
