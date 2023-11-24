# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from mako.template import Template
from giscedata_facturacio.report.utils import get_atr_price
from datetime import date


class ReportBackendMailcanvipreus(ReportBackend):
    _source_model = 'som.enviament.massiu'
    _name = 'report.backend.mailcanvipreus'

    @report_browsify
    def get_data(self, cursor, uid, env, context=None):
        if context is None:
            context = {}

        data = {
            'text_legal': self.get_text_legal(cursor, uid, env, context=context),
            'lang': env.polissa_id.titular.lang,
            'nom_titular': self.getPartnerName(cursor, uid, env),
            'te_gkwh': env.polissa_id.te_assignacio_gkwh,
        }
        data.update(self.getTarifaCorreu(cursor, uid, env, context))
        return data

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        env_o = self.pool.get('som.enviament.massiu')
        env_br = env_o.browse(cursor, uid, record_id, context=context)

        return env_br.polissa_id.titular.lang

    def getConsumEstimatPotencia(self, potencia):
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

    def calcularPreuTotal(self, cursor, uid, polissa_id, consums, potencies, tarifa, afegir_maj, bo_social_separat, date=None):
        ctx = {}
        if date:
            ctx['date'] = date
        ctx['potencia_anual'] = True
        ctx['sense_agrupar'] = True
        maj_price = 0.140  # €/kWh
        bo_social_price = 14.035934
        types = {
            'tp': potencies or {},
            'te': consums or {}
        }
        imports = 0
        for terme, values in types.items():
            for periode, quantity in values.items():
                preu_periode = get_atr_price(
                    cursor, uid, polissa_id, periode, terme, ctx, with_taxes=False
                )[0]
                if afegir_maj and terme == 'te':
                    preu_periode += maj_price
                imports += preu_periode * quantity
        if bo_social_separat:
            imports += bo_social_price

        return imports

    def aplicarCoeficients(consum_anual, tarifa):
        coeficients = {
            '2.0TD': {
                'P1': 0.284100158347879,
                'P2': 0.251934848093523,
                'P3': 0.463964993558617,
            },
            '3.0TD': {
                'P1': 0.1179061169783,
                'P2': 0.135534026607127,
                'P3': 0.126188472795622,
                'P4': 0.137245875258514,
                'P5': 0.052448855573218,
                'P6': 0.430676652787213,
            },
            '6.1TD': {
                'P1': 0.1179061169783,
                'P2': 0.135534026607127,
                'P3': 0.126188472795622,
                'P4': 0.137245875258514,
                'P5': 0.052448855573218,
                'P6': 0.430676652787213,
            },
            '3.0TDVE': {
                'P1': 0.112062097,
                'P2': 0.146848881,
                'P3': 0.137274931,
                'P4': 0.160997487,
                'P5': 0.066871062,
                'P6': 0.375945543
            },
        }
        consums = {
            k: consum_anual * coeficients[tarifa][k]
            for k in coeficients[tarifa].keys()
        }
        return consums

    def getConanyDict(self, cursor, uid, env):
        conany = {
            'P1': env.polissa_id.cups.conany_kwh_p1,
            'P2': env.polissa_id.cups.conany_kwh_p2,
            'P3': env.polissa_id.cups.conany_kwh_p3,
            'P4': env.polissa_id.cups.conany_kwh_p4,
            'P5': env.polissa_id.cups.conany_kwh_p5,
            'P6': env.polissa_id.cups.conany_kwh_p6,
        }
        return conany

    def calcularImpostos(preu, fiscal_position, potencies):
        iva = 0.21
        impost_electric = 0.05113
        if fiscal_position:
            if fiscal_position.id in [19, 33, 38]:
                iva = 0.03
            if fiscal_position.id in [25, 34, 39]:
                iva = 0.0
        preu_imp = round(preu * (1 + impost_electric), 2)
        return round(preu_imp * (1 + iva))

    def formatNumber(number):
        return format(number, "1,.0f").replace(',', '.')

    def restaCamps(self, cursor, uid, env):
        PRICE_CHANGE_DATE = '2024-01-01'

        potencies = self.getPotenciesPolissa(cursor, uid, env.polissa_id)

        tarifa = env.polissa_id.tarifa.name
        consums = ''
        origen = ''
        quintextes = ''
        if env.extra_text:
            consums = eval(env.extra_text)
            origen = consums['origen']
            quintextes = consums['origen']
            del consums['origen']
            consum_total = sum(consums.values())
        elif any([env.polissa_id.cups.conany_kwh_p1, env.polissa_id.cups.conany_kwh_p2, env.polissa_id.cups.conany_kwh_p3]):
            consums = self.getConanyDict()
            consum_total = env.polissa_id.cups.conany_kwh
            origen = env.polissa_id.cups.conany_origen
        else:
            consum_total = self.getConsumEstimatPotencia(env.polissa_id.potencia)
            consums = self.aplicarCoeficients(consum_total, tarifa)
            origen = 'estadistic'

        preu_vell = self.calcularPreuTotal(env.polissa_id, consums, potencies, tarifa, False,
                                           False, date.today().strftime("%Y-%m-%d"))
        preu_nou = self.calcularPreuTotal(env.polissa_id,
                                          consums, potencies, tarifa, False, True, PRICE_CHANGE_DATE)

        preu_vell_imp_int = self.calcularImpostos(
            preu_vell, env.polissa_id.fiscal_position_id, potencies)
        preu_nou_imp_int = self.calcularImpostos(
            preu_nou, env.polissa_id.fiscal_position_id, potencies)

        increment_total = self.formatNumber(abs(preu_nou_imp_int - preu_vell_imp_int))
        increment_mensual = abs((preu_nou_imp_int - preu_vell_imp_int) / 12)

        preu_vell_imp = self.formatNumber(preu_vell_imp_int)
        preu_nou_imp = self.formatNumber(preu_nou_imp_int)

        consum_total = self.formatNumber(round(consum_total / 100.0) * 100)

    def getIGIC(self, cursor, uid, env, context=False):
        if env.polissa_id.fiscal_position_id.id in [19, 33, 38]:
            return 3
        elif env.polissa_id.fiscal_position_id.id in [25, 34, 39]:
            return 0
        else:
            raise Exception("No té IGIC")

    def esCanaries(self, cursor, uid, env, context=False):
        return env.polissa_id.fiscal_position_id.id in [19, 33, 38, 25, 34, 39]

    def getTarifaCorreu(self, cursor, uid, env, context=False):
        data = {
            'Periodes20TDPeninsulaFins10kw': False,
            'Periodes20TDPeninsulaMesDe10kw': False,
            'Periodes20TDCanaries': False,
            'Periodes30i60TDPeninsula': False,
            'Periodes30i60TDCanaries': False,
            'igic': False,
            'Indexada20TDPeninsulaBalearsFins10kw': False,
            'Indexada20TDPeninsulaBalearsMesDe10kw': False,
            'Indexada20TDCanaries': False,
            'indexada': False,
            'periodes': False,
        }
        tarifa = env.polissa_id.tarifa.name
        potencies = self.getPotenciesPolissa(cursor, uid, env.polissa_id)

        if 'indexada' in tarifa:
            if '2.0TD' in tarifa:
                if self.esCanaries(cursor, uid, env):
                    data['Indexada20TDCanaries'] = True
                    data['igic'] = self.getIGIC(cursor, uid, env)
                else:
                    if int(potencies['P1']) < 10:
                        data['Indexada20TDPeninsulaBalearsFins10kw'] = True
                    else:
                        data['Indexada20TDPeninsulaBalearsMesDe10kw'] = True
            data['indexada'] = True
        else:
            if '2.0TD' in tarifa:
                if self.esCanaries(cursor, uid, env):
                    data['Periodes20TDCanaries'] = True
                    data['igic'] = self.getIGIC(cursor, uid, env)
                else:
                    if int(potencies['P1']) < 10:
                        data['Periodes20TDPeninsulaFins10kw'] = True
                    else:
                        data['Periodes20TDPeninsulaMesDe10kw'] = True
            elif '3.0TD' in tarifa or '6.1TD' in tarifa:
                if self.esCanaries(cursor, uid, env):
                    data['Periodes30i60TDCanaries'] = True
                else:
                    data['Periodes30i60TDPeninsula'] = True
            data['periodes'] = True
        return data

    def getPartnerName(self, cursor, uid, env):
        try:
            p_obj = env.pool.get('res.partner')
            if not p_obj.vat_es_empresa(env._cr, env._uid, env.polissa_id.titular.vat):
                nom_titular = ' ' + env.polissa_id.titular.name.split(',')[1].lstrip() + ','
            else:
                nom_titular = ','
        except:
            nom_titular = ','
        return nom_titular

    def get_text_legal(self, cursor, uid, env, context=None):
        def render(text_to_render, object_):
            templ = Template(text_to_render)
            return templ.render_unicode(
                object=object_,
                format_exceptions=True
            )

        if context is None:
            context = {}

        data = {}

        t_obj = self.pool.get('poweremail.templates')
        md_obj = self.pool.get('ir.model.data')

        template_id = md_obj.get_object_reference(
            cursor, uid, 'som_poweremail_common_templates', 'common_template_legal_footer'
        )[1]
        data['text_legal'] = render(t_obj.read(
            cursor, uid, [template_id], ['def_body_text'])[0]['def_body_text'], env
        )

        return data


ReportBackendMailcanvipreus()
