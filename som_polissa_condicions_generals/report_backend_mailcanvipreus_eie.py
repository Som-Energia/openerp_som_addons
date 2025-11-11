# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from giscedata_facturacio.report.utils import get_atr_price
from datetime import date, timedelta


class ReportBackendMailcanvipreusEiE(ReportBackend):
    _source_model = "som.enviament.massiu"
    _name = "report.backend.mailcanvipreus.eie"

    # nomes index
    indexada_consum_tipus = {
        "2.0TD": {
            "factor_eie_preu_antic": 133.781131630073,
            "factor_eie_preu_nou": 139.600101568505,
        },
        "3.0TD": {
            "factor_eie_preu_antic": 120.017809474036,
            "factor_eie_preu_nou": 125.837481976305,
        },
        "6.1TD": {
            "factor_eie_preu_antic": 106.055050891024,
            "factor_eie_preu_nou": 111.316018940409,
        },
        "3.0TDVE": {
            "factor_eie_preu_antic": 0,
            "factor_eie_preu_nou": 0,
        },
    }

    def get_fs(self, cursor, uid, env, context=None):
        if context is None:
            context = {}

        som_polissa_k_change_obj = self.pool.get("som.polissa.k.change")

        search_params = [
            ('polissa_id', '=', env.polissa_id.id)
        ]

        k_change_id = som_polissa_k_change_obj.search(
            cursor, uid, search_params, context=context
        )

        res = {'k_old': 0, 'k_new': 0}
        if k_change_id:
            res = som_polissa_k_change_obj.read(
                cursor, uid, k_change_id[0], ['k_old', 'k_new'], context=context
            )

        return res

    def is_eie(self, cursor, uid, env, context=None):
        if context is None:
            context = {}

        pol_llista = env.polissa_id.llista_preu.id

        return pol_llista in [150, 153, 154]

    def get_data_eie(self, cursor, uid, env, context=None):
        if context is None:
            context = {}

        data = {
            'cups': env.polissa_id.cups.name,
            'titular': env.polissa_id.titular.name,
            'numero': env.polissa_id.name
        }

        return data

    @report_browsify
    def calculate_new_eie_indexed_prices(self, cursor, uid, env, context=None):
        if context is None:
            context = {}

        f_antiga = self.get_fs(cursor, uid, env, context=context)['k_old']
        f_nova = self.get_fs(cursor, uid, env, context=context)['k_new']

        tarifa_acces = env.polissa_id.tarifa.name
        factor_eie_preu_antic = self.indexada_consum_tipus[tarifa_acces]["factor_eie_preu_antic"]
        factor_eie_preu_nou = self.indexada_consum_tipus[tarifa_acces]["factor_eie_preu_nou"]

        preu_mitja_antic = (1.015 * f_antiga + factor_eie_preu_antic) / 1000
        preu_mitja_nou = (1.015 * f_nova + factor_eie_preu_nou) / 1000

        conany = env.polissa_id.cups.conany_kwh if env.polissa_id.cups.conany_kwh > 0 else 1
        potencia = env.polissa_id.potencia
        preu_potencia = sum(self.get_preus(
            cursor, uid, env.polissa_id, with_taxes=True, context=context
        )['tp'].values())

        import_total_anual_antiga = (preu_mitja_antic * conany)
        import_total_anual_nova = (preu_mitja_nou * conany)
        impacte_import = import_total_anual_nova - import_total_anual_antiga

        import_total_anual_antiga_amb_impost = import_total_anual_antiga * 1.015 * 1.21
        import_total_anual_nova_amb_impost = import_total_anual_nova * 1.015 * 1.21
        impacte_import_amb_impost = (
            import_total_anual_nova_amb_impost - import_total_anual_antiga_amb_impost
        )
        impacte_perc = impacte_import_amb_impost / import_total_anual_antiga_amb_impost

        consum_eie = {
            "conany": conany,
            "pot_contractada": potencia,
            "preu_pot_contractada": preu_potencia,
            "factor_eie_preu_antic": factor_eie_preu_antic,
            "factor_eie_preu_nou": factor_eie_preu_nou,
            "f_antiga_eie": f_antiga / 1000,
            "f_nova_eie": f_nova / 1000,
            "preu_mig_anual_antiga": preu_mitja_antic,
            "preu_mig_anual_nova": preu_mitja_nou,
            "import_total_anual_antiga": import_total_anual_antiga,
            "import_total_anual_nova": import_total_anual_nova,
            "impacte_import": impacte_import,
            "impacte_perc": impacte_perc * 100,
            "iva": 21,
            "ie": 5.11,
            "import_total_anual_antiga_amb_impost": import_total_anual_antiga_amb_impost,
            "import_total_anual_nova_amb_impost": import_total_anual_nova_amb_impost,
            "impacte_import_amb_impost": impacte_import_amb_impost,
        }

        return consum_eie

    def get_preus(self, cursor, uid, pol, with_taxes=False, context=None):
        if context is None:
            context = {}
        context["potencia_anual"] = True

        result = {}
        periods = {
            "tp": sorted(pol.tarifa.get_periodes("tp", context=context).keys()),
            "te": sorted(pol.tarifa.get_periodes("te", context=context).keys()),
        }
        if (pol.modcontractuals_ids[0].state == "pendent"
            and pol.mode_facturacio
            != pol.modcontractuals_ids[0].mode_facturacio
                and pol.modcontractuals_ids[0].mode_facturacio == 'index'):
            context["force_pricelist"] = pol.modcontractuals_ids[1].llista_preu.id
        elif(pol.modcontractuals_ids[0].state == "pendent"
             and pol.mode_facturacio
             != pol.modcontractuals_ids[0].mode_facturacio
                and pol.modcontractuals_ids[0].mode_facturacio == 'atr'):
            context["force_pricelist"] = pol.modcontractuals_ids[0].llista_preu.id
        for terme, values in periods.items():
            result[terme] = {}
            for periode in values:
                preu_periode = get_atr_price(
                    cursor, uid, pol, periode, terme, context=context, with_taxes=with_taxes
                )[0]
                result[terme][periode] = preu_periode
        return result

    def getImpostos(self, fiscal_position, context=False):
        imp_str = "IVA del 10%" if context and context.get('iva10') else "IVA del 21%"
        imp_value = 21
        if fiscal_position:
            if fiscal_position.id in [33, 47, 56, 52, 61, 38, 21, 19, 87, 89, 94]:
                imp_str = "IGIC del 3%"
                imp_value = 3
            if fiscal_position.id in [34, 48, 53, 57, 53, 62, 39, 25, 88, 90]:
                imp_str = "IGIC del 0%"
                imp_value = 0
        return imp_str, float(imp_value)

    @report_browsify
    def get_data(self, cursor, uid, env, context=None):
        imd_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}

        impostos_str, impostos_value = self.getImpostos(env.polissa_id.fiscal_position_id, context)

        if impostos_str == 'IVA del 10%':
            fp_id = imd_obj.get_object_reference(
                cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
            context.update({'force_fiscal_position': fp_id})

        context_preus_antics = dict(context)
        context_preus_antics["date"] = date.today().strftime("%Y-%m-%d")

        context_preus_nous = dict(context)
        context_preus_nous["date"] = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")

        data = {
            "lang": env.polissa_id.titular.lang,
        }

        eie = self.is_eie(cursor, uid, env, context=context)
        if eie:
            data['dades_index'] = self.calculate_new_eie_indexed_prices(
                cursor, uid, env, context=context
            )
            data['contract'] = self.get_data_eie(cursor, uid, env, context=context)

        return data


ReportBackendMailcanvipreusEiE()
