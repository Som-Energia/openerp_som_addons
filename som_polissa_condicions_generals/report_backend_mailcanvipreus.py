# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from mako.template import Template
from giscedata_facturacio.report.utils import get_atr_price
from som_extend_facturacio_comer.utils import get_gkwh_atr_price
from datetime import date, timedelta


class ReportBackendMailcanvipreus(ReportBackend):
    _source_model = "som.enviament.massiu"
    _name = "report.backend.mailcanvipreus"

    _decimals = {
        ("preus_nous_generation", "P1"): 3,
        ("preus_nous_generation", "P2"): 3,
        ("preus_nous_generation", "P3"): 3,
        ("preus_nous_generation", "P4"): 3,
        ("preus_nous_generation", "P5"): 3,
        ("preus_nous_generation", "P6"): 3,
        ("preus_nous_generation_imp", "P1"): 3,
        ("preus_nous_generation_imp", "P2"): 3,
        ("preus_nous_generation_imp", "P3"): 3,
        ("preus_nous_generation_imp", "P4"): 3,
        ("preus_nous_generation_imp", "P5"): 3,
        ("preus_nous_generation_imp", "P6"): 3,
        ("preus_antics_generation", "P1"): 3,
        ("preus_antics_generation", "P2"): 3,
        ("preus_antics_generation", "P3"): 3,
        ("preus_antics_generation", "P4"): 3,
        ("preus_antics_generation", "P5"): 3,
        ("preus_antics_generation", "P6"): 3,
        ("preus_antics_generation_imp", "P1"): 3,
        ("preus_antics_generation_imp", "P2"): 3,
        ("preus_antics_generation_imp", "P3"): 3,
        ("preus_antics_generation_imp", "P4"): 3,
        ("preus_antics_generation_imp", "P5"): 3,
        ("preus_antics_generation_imp", "P6"): 3,
        ("preus_nous", "te", "P1"): 3,
        ("preus_nous", "te", "P2"): 3,
        ("preus_nous", "te", "P3"): 3,
        ("preus_nous", "te", "P4"): 3,
        ("preus_nous", "te", "P5"): 3,
        ("preus_nous", "te", "P6"): 3,
        ("preus_nous", "tp", "P1"): 3,
        ("preus_nous", "tp", "P2"): 3,
        ("preus_nous", "tp", "P3"): 3,
        ("preus_nous", "tp", "P4"): 3,
        ("preus_nous", "tp", "P5"): 3,
        ("preus_nous", "tp", "P6"): 3,
        ("preus_antics", "te", "P1"): 3,
        ("preus_antics", "te", "P2"): 3,
        ("preus_antics", "te", "P3"): 3,
        ("preus_antics", "te", "P4"): 3,
        ("preus_antics", "te", "P5"): 3,
        ("preus_antics", "te", "P6"): 3,
        ("preus_antics", "tp", "P1"): 3,
        ("preus_antics", "tp", "P2"): 3,
        ("preus_antics", "tp", "P3"): 3,
        ("preus_antics", "tp", "P4"): 3,
        ("preus_antics", "tp", "P5"): 3,
        ("preus_antics", "tp", "P6"): 3,
        ("preus_nous_imp", "te", "P1"): 3,
        ("preus_nous_imp", "te", "P2"): 3,
        ("preus_nous_imp", "te", "P3"): 3,
        ("preus_nous_imp", "te", "P4"): 3,
        ("preus_nous_imp", "te", "P5"): 3,
        ("preus_nous_imp", "te", "P6"): 3,
        ("preus_nous_imp", "tp", "P1"): 3,
        ("preus_nous_imp", "tp", "P2"): 3,
        ("preus_nous_imp", "tp", "P3"): 3,
        ("preus_nous_imp", "tp", "P4"): 3,
        ("preus_nous_imp", "tp", "P5"): 3,
        ("preus_nous_imp", "tp", "P6"): 3,
        ("preus_antics_imp", "te", "P1"): 3,
        ("preus_antics_imp", "te", "P2"): 3,
        ("preus_antics_imp", "te", "P3"): 3,
        ("preus_antics_imp", "te", "P4"): 3,
        ("preus_antics_imp", "te", "P5"): 3,
        ("preus_antics_imp", "te", "P6"): 3,
        ("preus_antics_imp", "tp", "P1"): 3,
        ("preus_antics_imp", "tp", "P2"): 3,
        ("preus_antics_imp", "tp", "P3"): 3,
        ("preus_antics_imp", "tp", "P4"): 3,
        ("preus_antics_imp", "tp", "P5"): 3,
        ("preus_antics_imp", "tp", "P6"): 3,
        ("dades_index", "f_antiga"): 3,
        ("dades_index", "f_nova"): 3,
        ("dades_index", "f_antiga_eie"): 6,
        ("dades_index", "f_nova_eie"): 6,
        ("preu_nou",): 0,
        ("preu_nou_imp",): 0,
        ("preu_vell",): 0,
        ("preu_vell_imp",): 0,
        ("consum_total",): 0,
        ("auto", "nous", "amb_impostos"): 3,
        ("auto", "nous", "sense_impostos"): 3,
        ("auto", "vells", "amb_impostos"): 3,
        ("auto", "vells", "sense_impostos"): 3,
    }

    indexada_consum_tipus = {
        "2.0TD": {
            "conany": 2500,
            "pot_contractada": 4.40,
            "preu_pot_contractada": 30.533,
            "f_antiga": 0.02,
            "f_nova": 0.02,
            "preu_mig_anual_antiga": 154.08,
            "preu_mig_anual_nova": 159.90,
            "import_total_anual_antiga": 519.55,
            "import_total_anual_nova": 534.10,
            "impacte_import": 14.55,
            "impacte_perc": 2.80,
            "factor_eie_preu_antic": 133.781131630073,
            "factor_eie_preu_nou": 139.600101568505,
            "iva": 21,
            "ie": 5.11,
            "import_total_anual_antiga_amb_impost": 660.78,
            "import_total_anual_nova_amb_impost": 679.28,
            "impacte_import_amb_impost": 18.50,
        },
        "3.0TD": {
            "conany": 10000,
            "pot_contractada": 14,
            "preu_pot_contractada": 37.89701,
            "f_antiga": 0.016,
            "f_nova": 0.016,
            "preu_mig_anual_antiga": 136.26,
            "preu_mig_anual_nova": 142.08,
            "import_total_anual_antiga": 1893.17,
            "import_total_anual_nova": 1951.37,
            "impacte_import": 58.20,
            "impacte_perc": 3.07,
            "factor_eie_preu_antic": 120.017809474036,
            "factor_eie_preu_nou": 125.837481976305,
            "iva": 21,
            "ie": 5.11,
            "import_total_anual_antiga_amb_impost": 2407.80,
            "import_total_anual_nova_amb_impost": 2481.81,
            "impacte_import_amb_impost": 74.02,
        },
        "6.1TD": {
            "conany": 15000,
            "pot_contractada": 20,
            "preu_pot_contractada": 62.382142,
            "f_antiga": 0.016,
            "f_nova": 0.016,
            "preu_mig_anual_antiga": 122.30,
            "preu_mig_anual_nova": 127.56,
            "import_total_anual_antiga": 3082.07,
            "import_total_anual_nova": 3160.98,
            "impacte_import": 78.91,
            "impacte_perc": 2.16,
            "factor_eie_preu_antic": 106.055050891024,
            "factor_eie_preu_nou": 111.316018940409,
            "iva": 21,
            "ie": 5.11,
            "import_total_anual_antiga_amb_impost": 3919.87,
            "import_total_anual_nova_amb_impost": 4020.24,
            "impacte_import_amb_impost": 100.37,
        },
        "3.0TDVE": {
            "conany": 10000,
            "pot_contractada": 14,
            "preu_pot_contractada": 7.005884,
            "f_antiga": 0.016,
            "f_nova": 0.016,
            "preu_mig_anual_antiga": 157.78,
            "preu_mig_anual_nova": 163.60,
            "import_total_anual_antiga": 1675.85,
            "import_total_anual_nova": 1734.05,
            "impacte_import": 58.20,
            "impacte_perc": 3.47,
            "factor_eie_preu_antic": 0,
            "factor_eie_preu_nou": 0,
            "iva": 21,
            "ie": 5.11,
            "import_total_anual_antiga_amb_impost": 2131.40,
            "import_total_anual_nova_amb_impost": 2205.42,
            "impacte_import_amb_impost": 74.02,
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

        return pol_llista in [56, 127, 128, 148]

    def get_data_eie(self, cursor, uid, env, context=None):
        if context is None:
            context = {}

        data = {
            'cups': env.polissa_id.cups.name,
            'direccio_cups': env.polissa_id.cups.direccio,
            'titular': env.polissa_id.titular.name,
            'numero': env.polissa_id.name
        }

        return data

    def calculate_new_indexed_prices(self, cursor, uid, env, is_canaries, imp_value, context=None):
        if context is None:
            context = {}

        data = self.indexada_consum_tipus[env.polissa_id.tarifa.name]
        if is_canaries:
            import_antiga = data["import_total_anual_antiga"]
            import_nova = data["import_total_anual_nova"]
            a = import_antiga * (1 + (imp_value / 100)) * (1 + 0.0511)
            n = import_nova * (1 + (imp_value / 100)) * (1 + 0.0511)
            impacte_amb_impostos = n - a
            data["iva"] = imp_value
            data["import_total_anual_antiga_amb_impost"] = a
            data["import_total_anual_nova_amb_impost"] = n
            data["impacte_import_amb_impost"] = impacte_amb_impostos
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

        # cost_potencia = preu_potencia * potencia

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

    @report_browsify
    def get_data(self, cursor, uid, env, context=None):
        imd_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}

        context['iva10'] = env.polissa_id.potencia <= 10

        impostos_str, impostos_value = self.getImpostos(env.polissa_id.fiscal_position_id, context)

        if impostos_str == 'IVA del 10%':
            fp_id = imd_obj.get_object_reference(
                cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
            context.update({'force_fiscal_position': fp_id})

        context_preus_antics = dict(context)
        context_preus_antics["date"] = date.today().strftime("%Y-%m-%d")

        context_preus_nous = dict(context)
        context_preus_nous["date"] = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")

        preus_antics = self.get_preus(
            cursor, uid, env.polissa_id, with_taxes=False, context=context_preus_antics
        )
        preus_nous = self.get_preus(
            cursor, uid, env.polissa_id, with_taxes=False, context=context_preus_nous
        )
        preus_antics_imp = self.get_preus(
            cursor, uid, env.polissa_id, with_taxes=True, context=context_preus_antics
        )
        preus_nous_imp = self.get_preus(
            cursor, uid, env.polissa_id, with_taxes=True, context=context_preus_nous
        )
        canaries = self.esCanaries(cursor, uid, env, context=context)
        balears = self.esBalears(cursor, uid, env, context=context)

        data = {
            "canaries": canaries,
            "balears": balears,
            "tarifa_acces": env.polissa_id.tarifa.name,
            "text_legal": self.get_text_legal(cursor, uid, env, context=context),
            "lang": env.polissa_id.titular.lang,
            "nom_titular": self.getPartnerName(cursor, uid, env),
            # "dades_index": self.calculate_new_indexed_prices(
            #     cursor, uid, env, canaries, impostos_value, context=context
            # ),
            "potencia": env.polissa_id.potencia,
            # "te_gkwh": env.polissa_id.te_assignacio_gkwh,
            "preus_antics": preus_antics,
            "preus_nous": preus_nous,
            "preus_antics_imp": preus_antics_imp,
            "preus_nous_imp": preus_nous_imp,
            "impostos_str": impostos_str,
            "modcon": (
                env.polissa_id.modcontractuals_ids[0].state == "pendent"
                and env.polissa_id.mode_facturacio
                != env.polissa_id.modcontractuals_ids[0].mode_facturacio
                and env.polissa_id.modcontractuals_ids[0].mode_facturacio
            ),
            'autoconsum': {
                'es_autoconsum': env.polissa_id.es_autoconsum,
                'compensacio': env.polissa_id.autoconsum_id.tipus_autoconsum in ['41', '42', '43']
            },
        }

        eie = self.is_eie(cursor, uid, env, context=context)
        if eie:
            data['dades_index'] = self.calculate_new_eie_indexed_prices(
                cursor, uid, env, context=context
            )
            data['contract'] = self.get_data_eie(cursor, uid, env, context=context)

        # if data["te_gkwh"]:
        #     data["preus_antics_generation"] = self.get_preus_gkwh(
        #         cursor, uid, env.polissa_id, with_taxes=False, context=context_preus_antics
        #     )
        #     data["preus_antics_generation_imp"] = self.get_preus_gkwh(
        #         cursor, uid, env.polissa_id, with_taxes=True, context=context_preus_antics
        #     )
        #     data["preus_nous_generation"] = self.get_preus_gkwh(
        #         cursor, uid, env.polissa_id, with_taxes=False, context=context_preus_nous
        #     )
        #     data["preus_nous_generation_imp"] = self.get_preus_gkwh(
        #         cursor, uid, env.polissa_id, with_taxes=True, context=context_preus_nous
        #     )

        data.update(self.getEstimacioData(cursor, uid, env, context=context_preus_nous))
        data.update(self.getTarifaCorreu(cursor, uid, env, context))
        # data.update(self.getPreuCompensacioExcedents(cursor, uid, env, context))
        return data

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        env_o = self.pool.get("som.enviament.massiu")
        env_br = env_o.browse(cursor, uid, record_id, context=context)

        return env_br.polissa_id.titular.lang

    def getConsumEstimatPotencia(self, potencia):  # noqa: C901
        res = 0
        if potencia <= 1:
            res = 200
        elif 1 < potencia <= 2:
            res = 600
        elif 2 < potencia <= 3:
            res = 1200
        elif 3 < potencia <= 4:
            res = 1800
        elif 4 < potencia <= 5:
            res = 2500
        elif 5 < potencia <= 6:
            res = 3100
        elif 6 < potencia <= 7:
            res = 4100
        elif 7 < potencia <= 8:
            res = 5000
        elif 8 < potencia <= 9:
            res = 5400
        elif 9 < potencia <= 10:
            res = 6100
        elif 10 < potencia <= 11:
            res = 7100
        elif 11 < potencia <= 12:
            res = 8500
        elif 12 < potencia <= 13:
            res = 9000
        elif 13 < potencia <= 14:
            res = 10000
        elif 14 < potencia <= 15:
            res = 10500
        elif potencia == 15.001:
            res = 9800
        elif 15.001 < potencia <= 20:
            res = 16500
        elif 20 < potencia <= 25:
            res = 22100
        elif 25 < potencia <= 30:
            res = 26500
        elif 30 < potencia <= 35:
            res = 33100
        elif 35 < potencia <= 40:
            res = 42500
        elif 40 < potencia <= 45:
            res = 48700
        elif 45 < potencia <= 50:
            res = 65400
        elif 50 < potencia <= 55:
            res = 52300
        elif 55 < potencia <= 60:
            res = 56100
        elif 60 < potencia <= 65:
            res = 62500
        elif 65 < potencia <= 70:
            res = 74800
        elif potencia > 70:
            res = 100000

        return res

    def getPotenciesPolissa(self, cursor, uid, pol):
        potencies = {}
        for pot in pol.potencies_periode:
            potencies[pot.periode_id.name] = pot.potencia
        return potencies

    def get_preus_gkwh(self, cursor, uid, pol, with_taxes=False, context=None):
        if context is None:
            context = {}

        result = {}

        gkwh_periodes = sorted(pol.tarifa.get_periodes("te", context=context).keys())
        for periode in gkwh_periodes:
            preu_periode = get_gkwh_atr_price(
                cursor, uid, pol, periode, context=context, with_taxes=with_taxes
            )[0]
            result[periode] = preu_periode
        return result

    def get_preus(self, cursor, uid, pol, with_taxes=False, context=None):
        if context is None:
            context = {}
        context["potencia_anual"] = True

        result = {}
        periods = {
            "tp": sorted(pol.tarifa.get_periodes("tp", context=context).keys()),
            "te": sorted(pol.tarifa.get_periodes("te", context=context).keys()),
            # 'ac': [sorted(pol.tarifa.get_periodes('te', context=context).keys())[0]], # not working for non auto pol  # noqa: E501
        }
        for terme, values in periods.items():
            result[terme] = {}
            for periode in values:
                preu_periode = get_atr_price(
                    cursor, uid, pol, periode, terme, context=context, with_taxes=with_taxes
                )[0]
                result[terme][periode] = preu_periode
        return result

    def preusEstimatsIndexada(self, cursor, uid, tarifa, periode):
        estimacions = {
            "2.0TD": {
                "P1": 0.243,
                "P2": 0.184,
                "P3": 0.148,
            },
            "3.0TD": {
                "P1": 0.216,
                "P2": 0.198,
                "P3": 0.169,
                "P4": 0.160,
                "P5": 0.145,
                "P6": 0.147,
            },
            "6.1TD": {
                "P1": 0.189,
                "P2": 0.176,
                "P3": 0.154,
                "P4": 0.152,
                "P5": 0.141,
                "P6": 0.141,
            },
            "3.0TDVE": {
                "P1": 0.216,
                "P2": 0.198,
                "P3": 0.169,
                "P4": 0.160,
                "P5": 0.145,
                "P6": 0.147,
            },
        }

        return estimacions[tarifa][periode]

    def getPreuCompensacioExcedents(self, cursor, uid, env, context):
        iva = 0.1 if context and context.get('iva10') else 0.21
        if env.polissa_id.fiscal_position_id:
            if env.polissa_id.fiscal_position_id.id in [33, 47, 52]:
                iva = 0.03
            if env.polissa_id.fiscal_position_id.id in [34, 48, 53]:
                iva = 0.0

        PREU_NOU = 0.06
        PREU_VELL = 0.07
        return {
            "auto": {
                "nous": {
                    "amb_impostos": PREU_NOU * 1.038 * (1 + iva),
                    "sense_impostos": PREU_NOU,
                },
                "vells": {
                    "amb_impostos": PREU_VELL * 1.025 * (1 + iva),
                    "sense_impostos": PREU_VELL,
                },
            }
        }

    def calcularPreuTotal(
        self,
        cursor,
        uid,
        polissa_id,
        consums,
        potencies,
        tarifa,
        afegir_maj,
        bo_social_separat,
        date=None,
        origen="",
    ):
        ctx = {}
        if date:
            ctx["date"] = date
        ctx["potencia_anual"] = True
        ctx["sense_agrupar"] = True
        maj_price = 0  # €/kWh
        bo_social_price = 2.299047
        types = {"tp": potencies or {}, "te": consums or {}}
        imports = 0
        for terme, values in types.items():
            for periode, quantity in values.items():
                preu_periode = get_atr_price(
                    cursor, uid, polissa_id, periode, terme, ctx, with_taxes=False
                )[0]
                if afegir_maj and terme == "te":
                    preu_periode += maj_price
                if terme == "te" and origen == "indexada":
                    preu_periode = self.preusEstimatsIndexada(cursor, uid, tarifa, periode)
                imports += preu_periode * quantity
        if bo_social_separat:
            imports += bo_social_price

        return imports

    def aplicarCoeficients(self, consum_anual, tarifa):
        coeficients = {
            "2.0TD": {
                "P1": 0.284100158347879,
                "P2": 0.251934848093523,
                "P3": 0.463964993558617,
            },
            "3.0TD": {
                "P1": 0.1179061169783,
                "P2": 0.135534026607127,
                "P3": 0.126188472795622,
                "P4": 0.137245875258514,
                "P5": 0.052448855573218,
                "P6": 0.430676652787213,
            },
            "6.1TD": {
                "P1": 0.1179061169783,
                "P2": 0.135534026607127,
                "P3": 0.126188472795622,
                "P4": 0.137245875258514,
                "P5": 0.052448855573218,
                "P6": 0.430676652787213,
            },
            "3.0TDVE": {
                "P1": 0.112062097,
                "P2": 0.146848881,
                "P3": 0.137274931,
                "P4": 0.160997487,
                "P5": 0.066871062,
                "P6": 0.375945543,
            },
        }
        consums = {k: consum_anual * coeficients[tarifa][k] for k in coeficients[tarifa].keys()}
        return consums

    def getConanyDict(self, cursor, uid, env):
        conany = {
            "P1": env.polissa_id.cups.conany_kwh_p1,
            "P2": env.polissa_id.cups.conany_kwh_p2,
            "P3": env.polissa_id.cups.conany_kwh_p3,
        }
        if env.polissa_id.tarifa_codi != "2.0TD":
            conany.update(
                {
                    "P4": env.polissa_id.cups.conany_kwh_p4,
                    "P5": env.polissa_id.cups.conany_kwh_p5,
                    "P6": env.polissa_id.cups.conany_kwh_p6,
                }
            )
        return conany

    def calcularImpostosPerCostAnualEstimat(self, preu, fiscal_position, context=False):
        iva = 0.1 if context and context.get('iva10') else 0.21
        impost_electric = 0.025
        if fiscal_position:
            if fiscal_position.id in [33, 47, 52]:
                iva = 0.03
            if fiscal_position.id in [34, 48, 53]:
                iva = 0.0
        preu_imp = round(preu * (1 + impost_electric), 2)
        return round(preu_imp * (1 + iva))

    def getImpostos(self, fiscal_position, context=False):
        imp_str = "IVA del 10%" if context and context.get('iva10') else "IVA del 21%"
        imp_value = 21
        if fiscal_position:
            if fiscal_position.id in [33, 47, 56, 52, 61, 38, 21, 19]:
                imp_str = "IGIC del 3%"
                imp_value = 3
            if fiscal_position.id in [34, 48, 53, 57, 53, 62, 39, 25]:
                imp_str = "IGIC del 0%"
                imp_value = 0
        return imp_str, float(imp_value)

    def formatNumber(self, number):
        return format(number, "1,.0f").replace(",", ".")

    def getEstimacioData(self, cursor, uid, env, context=False):
        PRICE_CHANGE_DATE = "2024-11-01"

        potencies = self.getPotenciesPolissa(cursor, uid, env.polissa_id)

        tarifa = env.polissa_id.tarifa.name
        mode_facturacio = env.polissa_id.mode_facturacio
        consums = ""
        origen = ""
        if "index" in mode_facturacio:
            origen = "indexada"
            consums = self.getConanyDict(cursor, uid, env)
            consum_total = env.polissa_id.cups.conany_kwh
        elif any(
            [
                env.polissa_id.cups.conany_kwh_p1,
                env.polissa_id.cups.conany_kwh_p2,
                env.polissa_id.cups.conany_kwh_p3,
            ]
        ):
            consums = self.getConanyDict(cursor, uid, env)
            consum_total = env.polissa_id.cups.conany_kwh
            origen = env.polissa_id.cups.conany_origen
        else:
            consum_total = self.getConsumEstimatPotencia(env.polissa_id.potencia)
            consums = self.aplicarCoeficients(consum_total, tarifa)
            origen = "estadistic"

        preu_vell = self.calcularPreuTotal(
            cursor,
            uid,
            env.polissa_id,
            consums,
            potencies,
            tarifa,
            False,
            True,
            date.today().strftime("%Y-%m-%d"),
            origen,
        )
        preu_nou = self.calcularPreuTotal(
            cursor,
            uid,
            env.polissa_id,
            consums,
            potencies,
            tarifa,
            False,
            True,
            PRICE_CHANGE_DATE,
            origen,
        )

        preu_vell_imp_int = self.calcularImpostosPerCostAnualEstimat(
            preu_vell, env.polissa_id.fiscal_position_id, context=context
        )
        preu_nou_imp_int = self.calcularImpostosPerCostAnualEstimat(
            preu_nou, env.polissa_id.fiscal_position_id, context=context
        )

        preu_vell_imp = self.formatNumber(preu_vell_imp_int)
        preu_nou_imp = self.formatNumber(preu_nou_imp_int)

        return {
            "origen": origen,
            "preu_vell": preu_vell,
            "preu_nou": preu_nou,
            "preu_vell_imp": preu_vell_imp,
            "preu_nou_imp": preu_nou_imp,
            "consum_total": consum_total,
            "potencia_max": env.polissa_id.potencia,
        }

    def getIGIC(self, cursor, uid, env, context=False):
        if env.polissa_id.fiscal_position_id.id in [33, 47, 52]:
            return 3
        elif env.polissa_id.fiscal_position_id.id in [34, 48, 53]:
            return 0
        else:
            raise Exception("Eh recorda actualitzar les posicions fiscals hardcodejades")

    def esCanaries(self, cursor, uid, env, context=False):
        return env.polissa_id.fiscal_position_id.id in [
            33, 34, 47, 56, 48, 57, 52, 61, 53, 62, 39, 38, 25, 21, 19
        ]

    def _get_list_cups_balears(self, cursor, uid, context=None):
        xml_id_prov_balears = "ES07"
        IrModel = self.pool.get("ir.model.data")
        id_prov_balears = IrModel._get_obj(
            cursor,
            uid,
            "l10n_ES_toponyms",
            xml_id_prov_balears,
        ).id

        sql_array = """
            select array_agg(gcp.id) as cup_ids
            from giscedata_cups_ps gcp
            inner join res_municipi rm on rm.id = gcp.id_municipi
            inner join res_country_state rcs on rcs.id = rm.state
            where rcs.id = %s and gcp.active=True
        """
        cursor.execute(sql_array, (id_prov_balears,))
        res = cursor.dictfetchone()["cup_ids"]
        return res or []

    def esBalears(self, cursor, uid, env, context=False):
        # return env.polissa_id.llista_preu.id in [127]
        return env.polissa_id.cups.id in self._get_list_cups_balears(cursor, uid)

    # def getTarifaCorreu(self, cursor, uid, env, context=False):
    #     data = {
    #         "Indexada20TDPeninsula": False,
    #         "Indexada20TDCanaries": False,
    #         "Indexada20TDBalears": False,
    #         "Indexada30TDPeninsula": False,
    #         "Indexada30TDCanaries": False,
    #         "Indexada30TDBalears": False,
    #         "Indexada61TDPeninsula": False,
    #         "Indexada61TDCanaries": False,
    #         "Indexada61TDBalears": False,
    #         "Indexada30TDVEPeninsula": False,
    #         "Indexada30TDVECanaries": False,
    #         "Indexada30TDVEBalears": False,
    #         "Periodes20TDPeninsula": False,
    #         "Periodes20TDCanaries": False,
    #         "Periodes20TDBalears": False,
    #         "Periodes30TDPeninsula": False,
    #         "Periodes30TDCanaries": False,
    #         "Periodes30TDBalears": False,
    #         "Periodes61TDPeninsula": False,
    #         "Periodes61TDCanaries": False,
    #         "Periodes61TDBalears": False,
    #         "Periodes30TDVEPeninsula": False,
    #         "Periodes30TDVECanaries": False,
    #         "Periodes30TDVEBalears": False,
    #         "igic": False,
    #         "indexada": False,
    #         "periodes": False,
    #     }
    #     mode_facturacio = env.polissa_id.mode_facturacio
    #     tarifa = env.polissa_id.tarifa.name

    #     if "index" in mode_facturacio:
    #         if "2.0TD" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Indexada20TDCanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Indexada20TDBalears"] = True
    #             else:
    #                 data['Indexada20TDPeninsula'] = True
    #         if "3.0TD" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Indexada30TDCanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Indexada30TDBalears"] = True
    #             else:
    #                 data["Indexada30TDPeninsula"] = True
    #         if "6.1TD" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Indexada61TDCanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Indexada61TDBalears"] = True
    #             else:
    #                 data["Indexada61TDPeninsula"] = True
    #         if "3.0TDVE" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Indexada30TDCanaries"] = False
    #                 data["Indexada30TDVECanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Indexada30TDBalears"] = False
    #                 data["Indexada30TDVEBalears"] = True
    #             else:
    #                 data["Indexada30TDPeninsula"] = False
    #                 data["Indexada30TDVEPeninsula"] = True
    #         data["indexada"] = True
    #     else:
    #         if "2.0TD" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Periodes20TDCanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Periodes20TDBalears"] = True
    #             else:
    #                 data['Periodes20TDPeninsula'] = True
    #         if "3.0TD" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Periodes30TDCanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Periodes30TDBalears"] = True
    #             else:
    #                 data["Periodes30TDPeninsula"] = True
    #         if "6.1TD" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Periodes61TDCanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Periodes61TDBalears"] = True
    #             else:
    #                 data["Periodes61TDPeninsula"] = True
    #         if "3.0TDVE" in tarifa:
    #             if self.esCanaries(cursor, uid, env):
    #                 data["Periodes30TDCanaries"] = False
    #                 data["Periodes30TDVECanaries"] = True
    #             elif self.esBalears(cursor, uid, env):
    #                 data["Periodes30TDBalears"] = False
    #                 data["Periodes30TDVEBalears"] = True
    #             else:
    #                 data["Periodes30TDPeninsula"] = False
    #                 data["Periodes30TDVEPeninsula"] = True
    #         data["periodes"] = True
    #     return data

    def getTarifaCorreu(self, cursor, uid, env, context=False):
        key_prefixes = ["Indexada", "Periodes"]
        tariffs = ["20TD", "30TD", "61TD", "30TDVE"]
        regions = ["Peninsula", "Canaries", "Balears"]

        data = {}
        for prefix in key_prefixes:
            for tariff in tariffs:
                for region in regions:
                    data["{}{}{}".format(prefix, tariff, region)] = False
        data.update({"igic": False, "indexada": False, "periodes": False})

        mode_facturacio = env.polissa_id.mode_facturacio
        tarifa = env.polissa_id.tarifa.name.replace(".", "")

        operation = "Indexada" if "index" in mode_facturacio else "Periodes"
        data[operation.lower()] = True

        for t in tariffs:
            if t in tarifa:
                if self.esCanaries(cursor, uid, env):
                    region_key = "Canaries"
                elif self.esBalears(cursor, uid, env):
                    region_key = "Balears"
                else:
                    region_key = "Peninsula"

                data["{}{}{}".format(operation, t, region_key)] = True

                if t == "30TDVE":
                    data["{}30TD{}".format(operation, region_key)] = False

                break

        return data

        # {'Indexada20TDBalears': False,
        # 'Indexada20TDCanaries': False,
        # 'Indexada20TDPeninsula': False,
        # 'Indexada30TDBalears': False,
        # 'Indexada30TDCanaries': False,
        # 'Indexada30TDPeninsula': False,
        # 'Indexada30TDVEBalears': False,
        # 'Indexada30TDVECanaries': False,
        # 'Indexada30TDVEPeninsula': False,
        # 'Indexada61TDBalears': False,
        # 'Indexada61TDCanaries': False,
        # 'Indexada61TDPeninsula': False,
        # 'Periodes20TDBalears': False,
        # 'Periodes20TDCanaries': False,
        # 'Periodes20TDPeninsula': False,
        # 'Periodes30TDBalears': False,
        # 'Periodes30TDCanaries': False,
        # 'Periodes30TDPeninsula': False,
        # 'Periodes30TDVEBalears': False,
        # 'Periodes30TDVECanaries': False,
        # 'Periodes30TDVEPeninsula': False,
        # 'Periodes61TDBalears': False,
        # 'Periodes61TDCanaries': False,
        # 'Periodes61TDPeninsula': False,
        # 'igic': False,
        # 'indexada': False,
        # 'periodes': False}

    def getPartnerName(self, cursor, uid, env):
        try:
            p_obj = env.pool.get("res.partner")
            if not p_obj.vat_es_empresa(env._cr, env._uid, env.polissa_id.titular.vat):
                nom_titular = " " + env.polissa_id.titular.name.split(",")[1].lstrip() + ","
            else:
                nom_titular = ","
        except Exception:
            nom_titular = ","
        return nom_titular

    def get_text_legal(self, cursor, uid, env, context=None):
        def render(text_to_render, object_):
            templ = Template(text_to_render)
            return templ.render_unicode(object=object_, format_exceptions=True)

        if context is None:
            context = {}

        t_obj = self.pool.get("poweremail.templates")
        md_obj = self.pool.get("ir.model.data")

        template_id = md_obj.get_object_reference(
            cursor, uid, "som_poweremail_common_templates", "common_template_legal_footer"
        )[1]
        data = render(
            t_obj.read(cursor, uid, [template_id], ["def_body_text"])[0]["def_body_text"], env
        )

        return data


ReportBackendMailcanvipreus()
