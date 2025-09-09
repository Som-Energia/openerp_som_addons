# -*- encoding: utf-8 -*-
from osv import osv
from tools.translate import _


class SomGurbWww(osv.osv_memory):

    _name = "som.gurb.www"

    def get_info_gurb(self, cursor, uid, gurb_code, tarifa_acces, context=None):

        gurb_group_obj = self.pool.get("som.gurb.group")
        gurb_group_ids = gurb_group_obj.search(cursor, uid, ('code', '=', gurb_code))
        if len(gurb_group_ids) == 0:
            return {
                "error": _("Cap Gurb Group amb el codi {}").format(gurb_code),
                "code": "BadGurbCode",
                "trace": "",
            }
        gurb_group_id = gurb_group_ids[0]

        if tarifa_acces not in ['2.0TD', '3.0TD']:
            return {
                "error": _("Tarifa d'accés no suportada '{}'").format(tarifa_acces),
                "code": "UnsuportedAccessTariff",
                "trace": "",
            }

        info = {}
        info['betes_disponibles'] = self._get_available_betas(
            cursor, uid, gurb_group_id, tarifa_acces, context)
        # info['compensacio_excedents'] = self._get_surplus_compensation(cursor, uid, gurb_group_id)
        # info['preu_entrada'] = self._get_initial_quota(cursor, uid, tarifa_acces, context)
        # info['quota'] = self._get_gurb_quota(cursor, uid, tarifa_acces, context)
        return info

    def _get_available_betas(self, cursor, uid, gurb_group_id, tarifa_acces, context=None):
        gurb_group_obj = self.pool.get("som.gurb.group")
        ggroup = gurb_group_obj.brrowse(cursor, uid, gurb_group_id, context=context)

        available_betas = []
        for gcau in ggroup.gurb_cau_ids:
            beta_remaining = gcau.generation_power
            for gcups in gcau.gurb_cups_ids:
                if gcups.state in ["active", "atr_pending"]:
                    beta_remaining -= gcups.future_beta_kw
                    beta_remaining -= gcups.future_gift_beta_kw
            available_betas.append(beta_remaining)

        max_available_beta = max(available_betas)
        max_power = ggroup.max_power_20 if tarifa_acces == '2.0TD' else ggroup.max_power_30
        power_limit = min(max_available_beta, max_power) if max_power else max_available_beta

        min_power = ggroup.min_power_20 if tarifa_acces == '2.0TD' else ggroup.min_power_30
        step = max(min_power, 0.05)

        betas = []
        while min_power <= power_limit:
            betas.append(min_power)
            min_power += step
        return betas
