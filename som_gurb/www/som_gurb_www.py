# -*- encoding: utf-8 -*-
from osv import osv
from tools.translate import _
from math import radians, cos, sin, asin, sqrt


def compute_haversine_distance(lat_gurb, long_gurb, lat_address, long_address):
    # Convert degrees to radians.
    long_address = radians(float(long_address))
    lat_address = radians(float(lat_address))

    long_gurb = radians(float(long_gurb))
    lat_gurb = radians(float(lat_gurb))

    # Haversine formula
    delta_long = long_address - long_gurb
    delta_lat = lat_address - lat_gurb
    hav = sin(delta_lat / 2)**2 + cos(lat_gurb) * cos(lat_address) * sin(delta_long / 2)**2

    # 6371 es el radi de la tierra en km
    return 2 * asin(sqrt(hav)) * 6371


class SomGurbWww(osv.osv_memory):

    _name = "som.gurb.www"

    supported_access_tariff = {
        '2.0TD': {
            'max_power': 'max_power_20',
            'min_power': 'min_power_20',
            'quota_product_name': 'product_gurb',
        },
        '3.0TD': {
            'max_power': 'max_power_30',
            'min_power': 'min_power_30',
            'quota_product_name': 'product_enterprise_gurb',
        },
    }

    def get_info_gurb(self, cursor, uid, gurb_code, tarifa_acces, context=None):

        gurb_group_obj = self.pool.get("som.gurb.group")
        gurb_group_ids = gurb_group_obj.search(cursor, uid, [('code', '=', gurb_code)])
        if len(gurb_group_ids) == 0:
            return {
                "error": _("Cap Gurb Group amb el codi {}").format(gurb_code),
                "code": "BadGurbCode",
                "trace": "",
            }
        gurb_group_id = gurb_group_ids[0]

        if tarifa_acces not in self.supported_access_tariff.keys():
            return {
                "error": _("Tarifa d'accés no suportada '{}'").format(tarifa_acces),
                "code": "UnsuportedAccessTariff",
                "trace": "",
            }

        info = self._get_quotas(
            cursor, uid, gurb_group_id, tarifa_acces, context=context)
        info['available_betas'] = self._get_available_betas(
            cursor, uid, gurb_group_id, tarifa_acces, context=context)
        info['surplus_compensation'] = self._get_surplus_compensation(
            cursor, uid, gurb_group_id, context=context)
        return info

    def check_coordinates_2km_validation(
        self, cursor, uid, lat_address, long_address, gurb_code, context=None
    ):
        if context is None:
            context = {}

        gurb_group_obj = self.pool.get("som.gurb.group")
        gurb_cau_obj = self.pool.get("som.gurb.cau")
        gurb_group_ids = gurb_group_obj.search(cursor, uid, [('code', '=', gurb_code)])
        if len(gurb_group_ids) == 0:
            return {
                "error": _("Cap Gurb Group amb el codi {}").format(gurb_code),
                "code": "BadGurbCode",
                "trace": "",
            }
        gurb_group_id = gurb_group_ids[0]

        gurb_cau_ids = gurb_cau_obj.search(cursor, uid, [('gurb_group_id', '=', gurb_group_id)])

        for gurb_cau_id in gurb_cau_ids:
            gurb_cau_br = gurb_cau_obj.browse(cursor, uid, gurb_cau_id, context=context)

            lat_gurb = gurb_cau_br.coordenada_latitud
            long_gurb = gurb_cau_br.coordenada_longitud

            distance_from_gurb = compute_haversine_distance(
                lat_gurb, long_gurb, lat_address, long_address
            )
            if distance_from_gurb < 1.9:
                return True

        return False

    def _get_available_betas(self, cursor, uid, gurb_group_id, tarifa_acces, context=None):
        gurb_group_obj = self.pool.get("som.gurb.group")
        ggroup = gurb_group_obj.browse(cursor, uid, gurb_group_id, context=context)

        available_betas = []
        for gcau in ggroup.gurb_cau_ids:
            beta_remaining = gcau.generation_power
            for gcups in gcau.gurb_cups_ids:
                if gcups.state in ["active", "atr_pending"]:
                    beta_remaining -= gcups.beta_kw
                    beta_remaining -= gcups.future_beta_kw
                    beta_remaining -= gcups.future_gift_beta_kw
            available_betas.append(beta_remaining)

        best_available_beta = max(available_betas) if available_betas else 0

        max_power_name = self.supported_access_tariff[tarifa_acces]['max_power']
        max_power = getattr(ggroup, max_power_name)
        min_power_name = self.supported_access_tariff[tarifa_acces]['min_power']
        min_power = getattr(ggroup, min_power_name)

        power_limit = min(best_available_beta, max_power) if max_power else best_available_beta
        step = max(min_power, 0.5)

        betas = []
        while min_power <= power_limit:
            betas.append(min_power)
            min_power += step
        return betas

    def _get_surplus_compensation(self, cursor, uid, gurb_group_id, context=None):
        gurb_group_obj = self.pool.get("som.gurb.group")
        ggroup = gurb_group_obj.browse(cursor, uid, gurb_group_id, context=context)

        surplus_compensation = []
        for gcau in ggroup.gurb_cau_ids:
            surplus_compensation.append(gcau.has_compensation)

        return any(surplus_compensation)

    def _get_quotas(self, cursor, uid, gurb_group_id, tarifa_acces, context=None):

        gurb_group_obj = self.pool.get("som.gurb.group")
        imd_obj = self.pool.get("ir.model.data")

        ggroup = gurb_group_obj.browse(cursor, uid, gurb_group_id, context=context)

        if not ggroup.pricelist_id:
            return {
                "error": _("Agurbació no te llista de preus {}").format(ggroup.code),
                "code": "GurbGroupWithoutPriceList",
                "trace": "",
            }

        initial_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "initial_quota_gurb"
        )[1]

        quota_product_name = self.supported_access_tariff[tarifa_acces]['quota_product_name']
        quota_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", quota_product_name
        )[1]

        initial = ggroup.pricelist_id.get_atr_price('tp', initial_product_id, False)
        quota = ggroup.pricelist_id.get_atr_price('tp', quota_product_id, False)

        return {
            'initial_quota': initial[0],
            'quota': quota[0],
        }


SomGurbWww()
