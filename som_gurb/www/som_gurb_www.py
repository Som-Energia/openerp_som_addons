# -*- encoding: utf-8 -*-
from osv import osv
from tools.translate import _
from math import radians, cos, sin, asin, sqrt
from datetime import datetime


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

        initial = ggroup.pricelist_id.get_atr_price(
            'tp', initial_product_id, False, with_taxes=True
        )
        quota = ggroup.pricelist_id.get_atr_price(
            'tp', quota_product_id, False, with_taxes=True
        )

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
            ("cups", "=", cups_id),
            ("state", "in", ["activa", "esborrany"]),
        ]
        polissa_ids = polissa_obj.search(
            cursor, uid, search_params, order="create_date DESC", limit=1
        )
        if polissa_ids:
            polissa_br = polissa_obj.browse(cursor, uid, polissa_ids[0], context=context)
            if polissa_br.state == "activa":
                sw_ids = sw_obj.search(cursor, uid, [
                    ('cups_polissa_id', '=', polissa_br.id),
                    ('state', '=', 'open'),
                    ('proces_id', 'not in', ["R1"])
                ])
                if sw_ids:
                    return False
            return polissa_ids[0]
        return None

    def activate_gurb_cups_lead(self, cursor, uid, gurb_lead_id, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")
        sign_docs_obj = self.pool.get("giscedata.signatura.documents")
        sign_process_obj = self.pool.get("giscedata.signatura.process")

        gurb_lead = gurb_cups_obj.browse(cursor, uid, gurb_lead_id, context=context)
        search_vals = [("model", "=", "som.gurb.cups,{}".format(gurb_lead_id))]
        doc_id = sign_docs_obj.search(cursor, uid, search_vals, limit=1)[0]
        process_id = sign_docs_obj.read(cursor, uid, doc_id, ["process_id"])["process_id"][0]

        sign_process_obj.update(cursor, uid, [process_id], context=context)

        sign_status = sign_process_obj.read(
            cursor, uid, process_id, ["status"], context=context
        )["status"]
        if gurb_lead.state != "draft":
            return {
                "success": False,
                "error": _("El gurb cups no està en estat esborrany"),
                "code": "GurbCupsNotDraft",
            }
        elif sign_status != "completed":
            return {
                "success": False,
                "error": _("La signatura no està completada"),
                "code": "SignatureNotCompleted",
            }
        else:
            gurb_cups_obj.send_signal(cursor, uid, [gurb_lead_id], "button_create_cups")
            return {"success": True}

    def _get_gurb_conditions_id(self, cursor, uid, pol_id, context=None):
        if context is None:
            context = {}
        pol_o = self.pool.get("giscedata.polissa")
        som_conditions_obj = self.pool.get("som.gurb.general.conditions")

        pol_br = pol_o.browse(cursor, uid, pol_id, context=context)
        lang_code = pol_br.titular.lang

        search_params = [("active", "=", True), ("lang_id.code", "=", lang_code)]

        conditions_ids = som_conditions_obj.search(
            cursor, uid, search_params, order="create_date DESC", limit=1
        )
        return conditions_ids[0] if conditions_ids else None

    def _get_signature_url(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}

        pro_obj = self.pool.get("giscedata.signatura.process")
        wiz_obj = self.pool.get("wizard.create.gurb.cups.signature")
        context["active_id"] = gurb_cups_id
        context["delivery_type"] = "url"
        context["sync"] = True

        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        process_id = wiz_obj.start_signature_process(cursor, uid, [wiz_id], context=context)

        if process_id:
            pro_br = pro_obj.browse(cursor, uid, process_id, context=context)
            return pro_br.signature_url
        return None

    def create_new_gurb_cups(self, cursor, uid, form_payload, context=None):
        if context is None:
            context = {}

        gurb_group_obj = self.pool.get("som.gurb.group")
        gurb_cups_obj = self.pool.get("som.gurb.cups")

        gurb_group_ids = gurb_group_obj.search(
            cursor, uid, [('code', '=', form_payload['gurb_code'])]
        )

        if len(gurb_group_ids) == 0:
            return {
                "success": False,
                "error": _("Cap Gurb Group amb el codi {}").format(form_payload['gurb_code']),
                "code": "BadGurbCode",
            }
        gurb_group_id = gurb_group_ids[0]
        beta = form_payload.get('beta', 0)

        gurb_cau_id = gurb_group_obj.get_prioritary_gurb_cau_id(
            cursor, uid, gurb_group_id, beta, context=context
        )
        if not gurb_cau_id:
            return {
                "success": False,
                "error": _("El gurb no té caus disponibles! {}").format(form_payload['gurb_code']),
                "code": "BadGurbGroup",
            }

        available_betas = self._get_available_betas(
            cursor, uid, gurb_group_id, form_payload['access_tariff'], context=context
        )
        if beta <= 0 or beta not in available_betas:
            return {
                "success": False,
                "error": _("La beta és incorrecta! {}").format(form_payload['beta']),
                "code": "BadBeta",
            }

        cups_id = self._get_cups_id(cursor, uid, form_payload["cups"], context=context)
        if not cups_id:
            return {
                "success": False,
                "error": _("No s'ha trobat el CUPS {}").format(form_payload["cups"]),
                "code": "BadCups",
            }

        polissa_id = self._get_polissa_id(cursor, uid, cups_id, context=context)
        if not polissa_id:
            return {
                "success": False,
                "error": _("No hi ha polissa o no està disponible"),
                "code": "ContractERROR",
            }

        beta_ids = [(0, 0, {
            "active": True,
            "start_date": datetime.strftime(datetime.today(), "%Y-%m-%d"),
            "beta_kw": beta,
            "extra_beta_kw": 0,
            "gift_beta_kw": 0,
            "future_beta": True
        })]

        # We create the new gurb cups and beta
        create_vals = {
            "active": True,
            "inscription_date": datetime.strftime(datetime.today(), "%Y-%m-%d"),
            "gurb_cau_id": gurb_cau_id,
            "cups_id": cups_id,
            "polissa_id": polissa_id,
            "betas_ids": beta_ids,
            "general_conditions_id": self._get_gurb_conditions_id(
                cursor, uid, polissa_id, context=context
            ),
        }
        gurb_cups_id = gurb_cups_obj.create(cursor, uid, create_vals, context=context)

        signature_url = self._get_signature_url(
            cursor, uid, gurb_cups_id, context=context
        )

        if gurb_cups_id:
            return {
                "success": True,
                "gurb_cups_id": gurb_cups_id,
                "signature_url": signature_url,
            }
        else:
            return {
                "success": False,
                "error": _("No s'ha pogut crear el GURB CUPS"),
                "code": "CreateGurbCupsError",
            }


SomGurbWww()
