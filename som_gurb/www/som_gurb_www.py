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

    def _get_cups_id(self, cursor, uid, cups_name, context=None):
        if context is None:
            context = {}
        cups_obj = self.pool.get("giscedata.cups.ps")
        try:
            cups_obj.check_cups_code(cursor, uid, cups_name, context=context)
        except osv.except_osv:
            return False
        cups_id = cups_obj.search(cursor, uid, [("name", "like", cups_name[:20])], limit=1)
        if cups_id:
            return cups_id[0]
        return None

    def _get_polissa_id(self, cursor, uid, cups_id, context=None):
        if context is None:
            context = {}
        polissa_obj = self.pool.get("giscedata.polissa")
        sw_obj = self.pool.get("giscedata.switching")
        search_params = [
            ("cups_id", "=", cups_id),
            ("state", "in", ["active", "draft"]),
        ]
        polissa_ids = polissa_obj.search(
            cursor, uid, search_params, order="create_date DESC", limit=1
        )
        if polissa_ids:
            polissa_br = polissa_obj.browse(cursor, uid, polissa_ids[0], context=context)
            if polissa_br.state == "active":
                sw_ids = sw_obj.search([
                    ('cups_polissa_id', '=', polissa_br.id),
                    ('state', '=', 'open'),
                    ('proces_id', 'not in', ["R1"])
                ])
                if sw_ids:
                    return False
            return polissa_ids[0]
        return None

    # def activate_gurb_cups_lead(self, cursor, uid, gurb_lead_id, context=None):

    def create_new_gurb_cups(self, cursor, uid, form_payload, context=None):
        if context is None:
            context = {}

        gurb_group_obj = self.pool.get("som.gurb.group")
        # gurb_cups_obj = self.pool.get("som.gurb.cups")

        beta = form_payload.get('beta', 0)
        if beta <= 0:
            return {
                "error": _("La beta ha de ser major que 0"),
                "code": "BadBeta",
                "trace": "",
            }

        gurb_group_ids = gurb_group_obj.search(
            cursor, uid, [('code', '=', form_payload['gurb_code'])]
        )
        if len(gurb_group_ids) == 0:
            return {
                "error": _("Cap Gurb Group amb el codi {}").format(form_payload['gurb_code']),
                "code": "BadGurbCode",
                "trace": "",
            }
        gurb_group_id = gurb_group_ids[0]

        gurb_cau_id = gurb_group_obj.get_prioritary_gurb_cau_id(
            cursor, uid, gurb_group_id, beta, context=context
        )
        if not gurb_cau_id:
            return {
                "error": _("El gurb grup no de caus! {}").format(form_payload['gurb_code']),
                "code": "BadGurbGroup",
                "trace": "",
            }

        cups_id = self._get_cups_id(cursor, uid, form_payload["cups"], context=context)
        if not cups_id:
            return {
                "error": _("No s'ha trobat el CUPS {}").format(form_payload["cups"]),
                "code": "BadCups",
                "trace": "",
            }

        polissa_id = self._get_polissa_id(cursor, uid, cups_id, context=context)
        if not polissa_id:
            return {
                "error": _("No hi ha polissa o no està disponible"),
                "code": "ContractERROR",
                "trace": "",
            }

        # We create the new gurb cups and beta
        # create_vals = {
        #     "active": True,
        #     "inscription_date": datetime.strftime(datetime.today(), "%Y-%m-%d"),
        #     "gurb_cau_id": gurb_cau_id,
        #     "cups_id": cups_id,
        #     "polissa_id": polissa_id,
        #     "betas_ids": "?",
        #     "initial_invoice_id": "?",
        #     "general_conditions_id": "?",
        #     "quota_product_id": "?",
        # }
        # gurb_cups_id = gurb_cups_obj.create(cursor, uid, create_vals, context=context)


SomGurbWww()
