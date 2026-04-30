# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from mako.template import Template
from giscedata_facturacio.report.utils import get_atr_price
from som_indexada.utils import calculate_new_indexed_prices
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
        ("preu_auto_antic", ): 3,
        ("preu_auto_nou", ): 3,
        ("preu_auto_antic_imp", ): 3,
        ("preu_auto_nou_imp", ): 3,
    }

    @report_browsify
    def get_data(self, cursor, uid, env, context=None):
        imd_obj = self.pool.get('ir.model.data')
        pol_obj = self.pool.get("giscedata.polissa")
        if context is None:
            context = {}

        context['iva10'] = env.polissa_id.potencia < 10

        self.simplified_taxes = pol_obj.get_simplified_taxes(
            cursor, uid, env.polissa_id.id, context=context)

        impostos_str = self.get_iva_text()

        if 'IVA' in self.simplified_taxes and self.simplified_taxes['IVA'] < 0.21:
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

        gurb = self.has_gurb(cursor, uid, env.polissa_id, context)

        canaries = self.esCanaries(cursor, uid, env, context=context)
        balears = self.esBalears(cursor, uid, env, context=context)

        data = {
            "codi_polissa": env.polissa_id.name,
            "canaries": canaries,
            "balears": balears,
            "tarifa_acces": env.polissa_id.tarifa.name,
            "mode_facturacio": env.polissa_id.mode_facturacio,
            "text_legal": self.get_text_legal(cursor, uid, env, context=context),
            "lang": env.polissa_id.titular.lang,
            "nom_titular": self.getPartnerName(cursor, uid, env),
            "iva_reduit": env.polissa_id.potencia < 10 and not canaries,
            "te_gkwh": env.polissa_id.te_assignacio_gkwh,
            "preus_antics": preus_antics,
            "preus_nous": preus_nous,
            "preus_antics_imp": preus_antics_imp,
            "preus_nous_imp": preus_nous_imp,
            "gurb": gurb,

            "impostos_str": impostos_str,
            "modcon": (
                env.polissa_id.modcontractuals_ids[0].state == "pendent"
                and env.polissa_id.mode_facturacio
                != env.polissa_id.modcontractuals_ids[0].mode_facturacio
                and env.polissa_id.modcontractuals_ids[0].mode_facturacio
            ),
            'autoconsum': {
                'es_autoconsum': env.polissa_id.es_autoconsum,
                'compensacio': env.polissa_id.tipus_subseccio in ['21']
            },
        }

        if data['autoconsum']['compensacio'] and data['mode_facturacio'] == 'atr':
            preu_auto_antic = get_atr_price(
                cursor, uid, env.polissa_id, 'P1', 'ac', context_preus_antics, with_taxes=False)[0]

            preu_auto_nou = get_atr_price(
                cursor, uid, env.polissa_id, 'P1', 'ac', context_preus_nous, with_taxes=False)[0]

            preu_auto_antic_imp = get_atr_price(
                cursor, uid, env.polissa_id, 'P1', 'ac', context_preus_antics, with_taxes=True)[0]

            preu_auto_nou_imp = get_atr_price(
                cursor, uid, env.polissa_id, 'P1', 'ac', context_preus_nous, with_taxes=True)[0]
            data['preu_auto_antic'] = preu_auto_antic
            data['preu_auto_nou'] = preu_auto_nou
            data['preu_auto_antic_imp'] = preu_auto_antic_imp
            data['preu_auto_nou_imp'] = preu_auto_nou_imp

        if data["te_gkwh"]:
            data["preus_antics_generation"] = self.get_preus_gkwh(
                cursor, uid, env.polissa_id, with_taxes=False, context=context_preus_antics
            )
            data["preus_antics_generation_imp"] = self.get_preus_gkwh(
                cursor, uid, env.polissa_id, with_taxes=True, context=context_preus_antics
            )
            data["preus_nous_generation"] = self.get_preus_gkwh(
                cursor, uid, env.polissa_id, with_taxes=False, context=context_preus_nous
            )
            data["preus_nous_generation_imp"] = self.get_preus_gkwh(
                cursor, uid, env.polissa_id, with_taxes=True, context=context_preus_nous
            )
            data.update(self.get_gkwh_estimation(cursor, uid, env, context=context_preus_nous))

        data.update(self.getEstimacioData(cursor, uid, env, context=context_preus_nous))
        data.update(self.getTarifaCorreu(cursor, uid, env, context))
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
            preu_periode = get_atr_price(
                cursor, uid, pol, periode, 'gkwh', context=context, with_taxes=with_taxes
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
        }
        if (pol.modcontractuals_ids[0].state == "pendent"
            and pol.mode_facturacio
            != pol.modcontractuals_ids[0].mode_facturacio
                and pol.modcontractuals_ids[0].mode_facturacio == 'index'):
            context["force_pricelist"] = pol.modcontractuals_ids[1].llista_preu.id
        elif (pol.modcontractuals_ids[0].state == "pendent"
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

    def calcularPreuTotal(
        self,
        cursor,
        uid,
        polissa_id,
        consums,
        potencies,
        afegir_servei_ajust,
        bo_social_separat,
        date=None,
        is_gkwh=False,
        context=None,
    ):
        conf_obj = self.pool.get('res.config')
        bo_social_price = self.get_bo_social_price(
            cursor, uid, polissa_id.llista_preu, context=context)
        preu_estimat_servei_ajust = float(
            conf_obj.get(cursor, uid, 'serveis_ajust_estimated_kwh_price'))

        ctx = context or {}
        if date:
            ctx["date"] = date
        ctx["potencia_anual"] = True
        ctx["sense_agrupar"] = True

        if is_gkwh:
            types = {'gkwh': consums or {}}
        else:
            types = {"tp": potencies or {}, "te": consums or {}}
            if (polissa_id.modcontractuals_ids[0].state == "pendent"
                    and polissa_id.mode_facturacio
                    != polissa_id.modcontractuals_ids[0].mode_facturacio
                    and polissa_id.modcontractuals_ids[0].mode_facturacio == 'index'):
                ctx["force_pricelist"] = polissa_id.modcontractuals_ids[1].llista_preu.id
            elif (polissa_id.modcontractuals_ids[0].state == "pendent"
                    and polissa_id.mode_facturacio
                    != polissa_id.modcontractuals_ids[0].mode_facturacio
                    and polissa_id.modcontractuals_ids[0].mode_facturacio == 'atr'):
                ctx["force_pricelist"] = polissa_id.modcontractuals_ids[0].llista_preu.id

        imports = 0
        for terme, values in types.items():
            for periode, quantity in values.items():
                preu_periode = get_atr_price(
                    cursor, uid, polissa_id, periode, terme, ctx, with_taxes=False
                )[0]
                if afegir_servei_ajust and terme != "tp":
                    preu_periode += preu_estimat_servei_ajust
                imports += preu_periode * quantity
        if bo_social_separat:
            imports += bo_social_price

        return imports

    _bo_social_price = False

    def get_bo_social_price(self, cursor, uid, pricelist, context=None):
        tarifa_obj = self.pool.get("giscedata.polissa.tarifa")
        if not self._bo_social_price:
            self._bo_social_price = (
                tarifa_obj.get_bo_social_price(cursor, uid, pricelist, context=context)[0]
            ) * 365
        return self._bo_social_price

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

    def calc_tax_for_anual_estimation(self, preu, context=None):
        iva = self.simplified_taxes.get('IGIC', self.simplified_taxes.get('IVA', 0.21))
        impost_electric = self.simplified_taxes.get('IE', 0)
        preu_imp = round(preu * (1 + impost_electric), 2)
        return round(preu_imp * (1 + iva))

    def get_iva_text(self, context=None):
        iva_str = 'IVA' if 'IVA' in self.simplified_taxes else 'IGIC'
        return '{} del {:.2f}%'.format(iva_str, self.simplified_taxes[iva_str] * 100)

    def has_gurb(self, cursor, uid, polissa, context=False):
        gurb_cups_obj = self.pool.get("som.gurb.cups")

        gurb_cups_id = gurb_cups_obj.search(cursor, uid, [("cups_id", "=", polissa.cups.id)])

        return gurb_cups_id

    def getEstimacioData(self, cursor, uid, env, context=False):
        potencies = self.getPotenciesPolissa(cursor, uid, env.polissa_id)

        tarifa = env.polissa_id.tarifa.name
        consums = ""
        origen = ""
        potencia = env.polissa_id.potencia
        if "index" in env.polissa_id.mode_facturacio:
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

        if origen == "indexada":
            dades_index = calculate_new_indexed_prices(cursor, uid, env.polissa_id, context=context)
            preu_vell = dades_index["import_total_anual_antiga"]
            preu_nou = dades_index["import_total_anual_nova"]
            preu_vell_imp = dades_index["import_total_anual_antiga_amb_impost"]
            preu_nou_imp = dades_index["import_total_anual_nova_amb_impost"]
        else:
            preu_vell = self.calcularPreuTotal(
                cursor,
                uid,
                env.polissa_id,
                consums,
                potencies,
                afegir_servei_ajust=False,
                bo_social_separat=True,
                date=date.today().strftime("%Y-%m-%d"),
                context=context,
            )
            preu_nou = self.calcularPreuTotal(
                cursor,
                uid,
                env.polissa_id,
                consums,
                potencies,
                afegir_servei_ajust=True,
                bo_social_separat=True,
                date=self.get_price_change_date(cursor, uid, env.polissa_id, context),
                context=context,
            )

            preu_vell_imp = self.calc_tax_for_anual_estimation(preu_vell)
            preu_nou_imp = self.calc_tax_for_anual_estimation(preu_nou)

        return {
            "origen": origen,
            "preu_vell": preu_vell,
            "preu_nou": preu_nou,
            "preu_vell_imp": preu_vell_imp,
            "preu_nou_imp": preu_nou_imp,
            "consum_total": consum_total,
            "potencia": potencia,
        }

    def get_gkwh_estimation(self, cursor, uid, env, context=False):
        pol_o = self.pool.get("giscedata.polissa")

        consums, origen = pol_o.generationkwh_anual_estimation(
            cursor, uid, env.polissa_id.id, context=context)

        if origen == 'no_data':
            consum_total = False
            preu_vell = False
            preu_nou = False
            preu_vell_imp = False
            preu_nou_imp = False
        else:
            consum_total = sum(quantity for _, quantity in consums.items())

            preu_vell = self.calcularPreuTotal(
                cursor,
                uid,
                env.polissa_id,
                consums,
                {},
                afegir_servei_ajust=False,
                bo_social_separat=False,
                date=date.today().strftime("%Y-%m-%d"),
                is_gkwh=True,
                context=context,
            )
            preu_nou = self.calcularPreuTotal(
                cursor,
                uid,
                env.polissa_id,
                consums,
                {},
                afegir_servei_ajust=True,
                bo_social_separat=False,
                date=self.get_price_change_date(cursor, uid, env.polissa_id, context),
                is_gkwh=True,
                context=context,
            )

            preu_vell_imp = self.calc_tax_for_anual_estimation(preu_vell)
            preu_nou_imp = self.calc_tax_for_anual_estimation(preu_nou)

        return {
            "gkwh_estimation": {
                "origen": origen,
                "preu_vell": preu_vell,
                "preu_nou": preu_nou,
                "preu_vell_imp": preu_vell_imp,
                "preu_nou_imp": preu_nou_imp,
                "consum_total": consum_total,
            }
        }

    def get_price_change_date(self, cursor, uid, polissa, context=None):
        today = date.today().strftime("%Y-%m-%d")
        if polissa.llista_preu:
            versions = polissa.llista_preu.version_id
            for version in versions:
                if version.active and version.date_start and version.date_start > today:
                    return version.date_start
        return (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")

    def esCanaries(self, cursor, uid, env, context=False):
        return env.polissa_id.cups.id_municipi.subsistema_id.code in [
            'TF', 'PA', 'LG', 'HI', 'GC', 'FL'
        ]

    def esBalears(self, cursor, uid, env, context=False):
        return env.polissa_id.cups.id_municipi.subsistema_id.code in ['MM', 'IF']

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

    def getPartnerName(self, cursor, uid, env):
        try:
            p_obj = env.pool.get("res.partner")
            if not p_obj.vat_es_empresa(env._cr, env._uid, env.polissa_id.titular.vat):
                nom_titular = " " + env.polissa_id.titular.name.split(",")[1].strip() + ","
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
