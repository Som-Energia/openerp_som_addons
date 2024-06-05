# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser
from datetime import datetime
from gestionatr.defs import TABLA_9
from giscedata_facturacio.report.utils import get_atr_price, get_comming_atr_price
from som_extend_facturacio_comer.utils import get_gkwh_atr_price
from tools.translate import _
from giscedata_polissa.report.utils import localize_period


TABLA_113_dict = {  # Table extracted from gestionatr.defs TABLA_113, not imported due translations issues # noqa: E501
    '00': _(u"Sense Autoconsum"),
    '01': _(u"Autoconsum Tipus 1"),
    '2A': _(u"Autoconsum tipus 2 (segons l'Art. 13. 2. a) RD 900/2015)"),
    '2B': _(u"Autoconsum tipus 2 (segons l'Art. 13. 2. b) RD 900/2015)"),
    '2G': _(u"Serveis auxiliars de generació lligada a un autoconsum tipus 2"),
    '31': _(u"Sense Excedents Individual - Consum"),
    '32': _(u"Sense Excedents Col·lectiu - Consum"),
    '33': _(u"Sense Excedents Col·lectiu amb acord de compensació – Consum"),
    '41': _(u"Amb excedents i compensació Individual-Consum"),
    '42': _(u"Amb excedents i compensació Col·lectiu-Consum"),
    '43': _(u"Amb excedents i compensació Col·lectiu a través de xarxa - Consum"),
    '51': _(u"Amb excedents sense compensació Individual sense cte. de Serv. Aux. en Xarxa Interior - Consum"),  # noqa: E501
    '52': _(u"Amb excedents sense compensació Col·lectiu sense cte. de Serv. Aux. en Xarxa Interior - Consum"),  # noqa: E501
    '53': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. en Xarxa Interior - Consum"),  # noqa: E501
    '54': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. en Xarxa Interior - Serv. Aux."),  # noqa: E501
    '55': _(u"Amb excedents sense compensació Col·lectiu / en Xarxa Interior - Consum"),
    '56': _(u"Amb excedents sense compensació Col·lectiu / en Xarxa Interior - Serv. Aux."),
    '61': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. a través de xarxa - Consum"),  # noqa: E501
    '62': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. a través de xarxa - Serv. Aux."),  # noqa: E501
    '63': _(u"Amb excedents sense compensació Col·lectiu a través de xarxa - Consum"),
    '64': _(u"Amb excedents sense compensació Col·lectiu a través de xarxa - Serv. Aux."),
    '71': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Consum"),  # noqa: E501
    '72': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Serv. Aux."),  # noqa: E501
    '73': _(u"Amb excedents sense compensació Col·lectiu amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Consum"),  # noqa: E501
    '74': _(u"Amb excedents sense compensació Col·lectiu amb cte. de Serv. Aux. a través de xarxa i xarxa interior - SSAA"),  # noqa: E501
}

CONTRACT_TYPES = dict(TABLA_9)

# def clean_text(text):
#     return text or ''


class ReportBackendCondicionsParticulars(ReportBackend):
    _source_model = "giscedata.polissa"
    _name = "report.backend.condicions.particulars"

    # _decimals = {
    #     ('potencia', 'potencies_contractades'): 0,
    # }

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        pol_o = self.pool.get("giscedata.polissa")
        sw_o = self.pool.get("giscedata.switching")
        lang = pol_o.browse(cursor, uid, record_id,  context=context).titular.lang
        return lang

    def get_pas01(self, cursor, uid, pol, context=None):
        sw_obj = self.pool.get("giscedata.switching")
        m1_id = context.get("m1_id")
        cas = sw_obj.browse(cursor, uid, m1_id)
        for step_id in cas.step_ids:
            proces_name = step_id.proces_id.name
            step_name = step_id.step_id.name
            if proces_name == "M1" and step_name == "01":
                return step_id
        return None

    # quan el cridem des del 01 fet la lògica a l'altre report perquè també sigui la que toca
    @report_browsify
    def get_data(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}
        if context.get("m1_id", False):
            pas01 = self.get_pas01(cursor, uid, pol, context)
        else:
            pas01 = False

        data = {
            "titular": self.get_titular_data(cursor, uid, pol, pas01, context=context),
            "potencies": self.get_potencies_data(cursor, uid, pol, pas01, context=context),
            "polissa": self.get_polissa_data(cursor, uid, pol, context=context),
            "cups": self.get_cups_data(cursor, uid, pol, context=context),
            "prices": self.get_prices_data(cursor, uid, pol, context=context),
        }
        return data

    def get_titular_data(self, cursor, uid, pol, pas01, context=None):
        if context is None:
            context = {}

        res = {}
        if pas01:
            m101_obj = self.pool.get("giscedata.switching.m1.01")
            pas_id = pas01.pas_id.split(",")[1]
            pas = m101_obj.browse(cursor, uid, pas_id)
            dades_client = pas.dades_client
            dades_envio = pas.direccio_notificacio
            es_ct_subrogacio = pas.sollicitudadm == "S" and pascanvi_titular == "S"
        else:
            dades_client = False
            dades_envio = False
            es_ct_subrogacio = False

        res['client_name'] = dades_client.name if es_ct_subrogacio and dades_client else pol.titular.name  # noqa: E501
        client_vat = dades_client.vat if es_ct_subrogacio and dades_client else pol.titular.vat  # noqa: E501
        res['client_vat'] = client_vat.replace('ES', '')
        direccio_titular = dades_client.address[0] if es_ct_subrogacio and dades_client else pol.titular.address[0]  # noqa: E501
        res['direccio_titular'] = direccio_titular
        direccio_envio = dades_envio if es_ct_subrogacio and dades_envio else pol.direccio_notificacio  # noqa: E501
        res['direccio_envio'] = direccio_envio
        res['diferent'] = (direccio_envio != direccio_titular)
        res['street'] = direccio_titular.street or ''
        res['zip'] = direccio_titular.zip or ''
        res['city'] = direccio_titular.city or ''
        res['state'] = direccio_titular.state_id.name or ''
        res['country'] = direccio_titular.country_id.name or ''
        res['email'] = direccio_titular.email or ''
        res['mobile'] = direccio_titular.mobile or ''
        res['phone'] = direccio_titular.phone or ''
        res['diferent'] = (direccio_envio != direccio_titular)
        res['name_envio'] = direccio_envio.name or ''
        res['street_envio'] = direccio_envio.street or ''
        res['zip_envio'] = direccio_envio.zip or ''
        res['city_envio'] = direccio_envio.city or ''
        res['state_envio'] = direccio_envio.state_id.name or ''
        res['country_envio'] = direccio_envio.country_id.name or ''
        res['email_envio'] = direccio_envio.email or ''
        res['mobile_envio'] = direccio_envio.mobile or ''
        res['phone_envio'] = direccio_envio.phone or ''
        data_firma = datetime.today()
        res['sign_date'] = localize_period(data_firma, pol.titular.lang)

        return res

    def get_potencies_data(self, cursor, uid, pol, pas01, context=None):
        res = {}
        if pas01:
            m101_obj = self.pool.get("giscedata.switching.m1.01")
            pas_id = pas01.pas_id.split(",")[1]
            pas = m101_obj.browse(cursor, uid, pas_id)
            es_canvi_tecnic = pas.sollicitudadm == "N"
        else:
            es_canvi_tecnic = False
        res['potencies'] = pas.pot_ids if es_canvi_tecnic else pol.potencies_periode
        res['autoconsum'] = pas.tipus_autoconsum if es_canvi_tecnic else pol.autoconsumo
        if res['autoconsum'] and res['autoconsum'] in TABLA_113_dict:
            res['autoconsum'] = TABLA_113_dict[res['autoconsum']]
        res['es_canvi_tecnic'] = es_canvi_tecnic
        pots = res['potencies']
        periodes = []
        for i in range(0, 6):
            if i < len(pots):
                periode = pots[i]
            else:
                periode = False
            periodes.append((i + 1, periode))

        if pol.tarifa_codi == "2.0TD":
            periodes[2] = periodes[1]
            periodes[1] = False
        res['periodes'] = periodes

        return res

    def get_polissa_data(self, cursor, uid, pol, context=None):
        pol_o = self.pool.get('giscedata.polissa')
        llista_preu_o = self.pool.get('product.pricelist')
        imd_obj = self.pool.get('ir.model.data')
        polissa = pol_o.browse(cursor, uid, pol.id)
        res = {}
        res['data_final'] = pol.modcontractual_activa.data_final or ''
        res['data_inici'] = pol.data_alta or ''
        res['name'] = pol.name
        res['state'] = pol.state
        res['lead'] = context.get('lead', False)
        res['auto'] = pol.autoconsumo
        res['contract_type'] = CONTRACT_TYPES[pol.contract_type]
        res['tarifa'] = pol.tarifa_codi
        res['data_baixa'] = pol.data_baixa
        # res['fiscal_poisition'] = pol.fiscal_poisition
        res['potencia_max'] = pol.potencia
        res['mode_facturacio'] = pol.mode_facturacio

        res['te_assignacio_gkwh'] = pol.te_assignacio_gkwh
        res['bank'] = pol.bank
        iban = pol.bank and pol.bank.printable_iban[5:] or ''
        res['printable_iban'] = iban[-4:]

        # context['potencia_anual'] = True
        # context['sense_agrupar'] = True
        res['periodes_energia'] = sorted(pol.tarifa.get_periodes(context=context).keys())
        res['periodes_potencia'] = sorted(pol.tarifa.get_periodes('tp', context=context).keys())

        polissa_categ_obj = self.pool.get('giscedata.polissa.category')
        polissa_categ_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa', 'categ_tarifa_empresa'
        )[1]
        pol_categ = polissa_categ_obj.browse(cursor, uid, polissa_categ_id)
        if pol_categ in pol.category_id:
            res['is_business'] = True
        else:
            res['is_business'] = False

        if pol.state == 'esborrany':
            res['modcon_pendent_indexada'] = False
            res['modcon_pendent_periodes'] = False
        elif pol.state != 'esborrany' and not res['lead']:
            res['last_modcon_state'] = pol.modcontractuals_ids[0].state
            res['last_modcon_facturacio'] = pol.modcontractuals_ids[0].mode_facturacio
            res['modcon_pendent_indexada'] = res['last_modcon_state'] == 'pendent' and res['last_modcon_facturacio'] == 'index'  # noqa: E501
            res['modcon_pendent_periodes'] = res['last_modcon_state'] == 'pendent' and res['last_modcon_facturacio'] == 'atr'  # noqa: E501
            res['last_modcon_pricelist'] = pol.modcontractuals_ids[0].llista_preu

        if res['modcon_pendent_indexada'] or res['modcon_pendent_periodes']:
            res['pricelist'] = pol.modcontractuals_ids[0].llista_preu
        elif pol.llista_preu:
            res['pricelist'] = pol.llista_preu
        else:
            tarifes_ids = llista_preu_o.search(cursor, uid, [])
            res['pricelist'] = pol_o.escull_llista_preus(cursor, uid, pol.id, tarifes_ids, context=context)  # noqa: E501

        if context.get('tarifa_provisional', False):
            res['tarifa_mostrar'] = 'Tarifa Períodes Empresa'
        else:
            res['tarifa_mostrar'] = res['pricelist'].nom_comercial or res['pricelist'].name

        coeficient_k = (pol.coeficient_k + pol.coeficient_d) / 1000
        res['mostra_indexada'] = False
        if polissa.mode_facturacio == 'index' and not res['modcon_pendent_periodes'] or res['modcon_pendent_indexada']:  # noqa: E501
            res['mostra_indexada'] = True
            if coeficient_k == 0:
                today = datetime.today().strftime("%Y-%m-%d")
                vlp = None
                if res['modcon_pendent_indexada']:
                    llista_preus = polissa.modcontractuals_ids[0].llista_preu.version_id
                else:
                    llista_preus = polissa.llista_preu.version_id
                for lp in llista_preus:
                    if lp.date_start <= today and (not lp.date_end or lp.date_end >= today):
                        vlp = lp
                        break
                if vlp:
                    for item in vlp.items_id:
                        if item.name == 'Coeficient K':
                            coeficient_k = item.base_price
                            break
        res['coeficient_k'] = coeficient_k

        # pol.pagador.name if not pas01 else dict_titular['client_name']
        return res

    def get_cups_data(self, cursor, uid, pol, context=None):
        res = {}
        res['direccio'] = pol.cups.direccio
        res['provincia'] = pol.cups.id_provincia.name
        res['country'] = pol.cups.id_provincia.country_id.name
        res['name'] = pol.cups.name
        res['cnae'] = pol.cnae.name
        res['ref_dist'] = pol.ref_dist or ''
        res['cnae_des'] = pol.cnae.descripcio
        res['distri'] = pol.cups.distribuidora_id.name
        res['tensio'] = pol.tensio or ''

        return res

    def get_prices_data(self, cursor, uid, pol, context=None):  # noqa: C901
        res = {}
        lead = context.get('lead')
        dict_preus_tp_potencia = False
        dict_preus_tp_energia = False
        omie_obj = self.pool.get('giscedata.monthly.price.omie')
        pol_obj = self.pool.get('giscedata.polissa')
        cfg_obj = self.pool.get('res.config')
        polissa = pol_obj.browse(cursor, uid, pol.id)
        if context.get('tarifa_provisional', False):
            dict_preus_tp_energia = context.get('tarifa_provisional')['preus_provisional_energia']
            if context.get('tarifa_provisional', False):
                if context['tarifa_provisional'].get('preus_provisional_potencia'):
                    dict_preus_tp_potencia = context['tarifa_provisional']['preus_provisional_potencia']  # noqa: E501

        res['dict_preus_tp_energia'] = dict_preus_tp_energia
        res['dict_preus_tp_potencia'] = dict_preus_tp_potencia

        ctx = {'date': datetime.today()}
        if polissa.data_baixa:
            ctx = {'date': datetime.strptime(polissa.data_baixa, '%Y-%m-%d')}
        if not pol.llista_preu:
            tarifes_a_mostrar = []
            if dict_preus_tp_potencia:
                tarifes_a_mostrar = [dict_preus_tp_potencia]
        else:
            tarifes_a_mostrar = get_comming_atr_price(cursor, uid, polissa, ctx)
        tarifes_a_mostrar if isinstance(tarifes_a_mostrar, list) else [tarifes_a_mostrar]

        res['pricelists'] = []
        for dades_tarifa in tarifes_a_mostrar:
            text_vigencia = ''
            pricelist = {}

            if pol.state != 'esborrany':
                ultima_modcon = pol.modcontractuals_ids[0]
                modcon_pendent_indexada = ultima_modcon.state == 'pendent' and \
                    ultima_modcon.mode_facturacio == 'index'
                modcon_pendent_periodes = ultima_modcon.state == 'pendent' and \
                    ultima_modcon.mode_facturacio == 'atr'

            if pol.state == 'esborrany':
                text_vigencia = ''
            elif modcon_pendent_indexada or modcon_pendent_periodes or lead:
                text_vigencia = ''
            elif not pol.modcontractual_activa.data_final and dades_tarifa['date_end']:
                text_vigencia = _(u"(vigents fins al {})").format(dades_tarifa['date_end'])
            elif dades_tarifa['date_end'] and dades_tarifa['date_start']:
                text_vigencia = _(u"(vigents fins al {})").format(
                    (datetime.strptime(dades_tarifa['date_end'], '%Y-%m-%d')).strftime('%d/%m/%Y'))
            elif datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d') > datetime.today():
                text_vigencia = _(u"(vigents a partir del {})").format(
                    datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d').strftime('%d/%m/%Y'))
            pricelist['text_vigencia'] = text_vigencia

            try:
                omie_mon_price_45 = omie_obj.has_to_charge_10_percent_requeriments_oficials(
                    cursor, uid, ctx['date'], pol.potencia)
            except Exception:
                omie_mon_price_45 = False
            pricelist['omie_mon_price_45'] = omie_mon_price_45

            start_date_iva_10 = cfg_obj.get(
                cursor, uid, 'charge_iva_10_percent_when_start_date', '2021-06-01'
            )
            end_date_iva_10 = cfg_obj.get(
                cursor, uid, 'iva_reduit_get_tariff_prices_end_date', '2024-12-31'
            )
            iva_10_active = eval(cfg_obj.get(
                cursor, uid, 'charge_iva_10_percent_when_available', '0'
            ))

            text_impostos = ''
            if not pol.fiscal_position_id and not lead:
                if iva_10_active and pol.potencia <= 10 and dades_tarifa['date_start'] >= start_date_iva_10 and dades_tarifa['date_start'] <= end_date_iva_10 and omie_mon_price_45:  # noqa: E501
                    # fp_id = imd_obj.get_object_reference(
                    #     cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
                    text_impostos = " (IVA 10%, IE 3,8%)"
                else:
                    # fp_id = imd_obj.get_object_reference(
                    #     cursor, uid, 'giscedata_facturacio_iese', 'fp_nacional_2024_rdl_8_2023_38')[1] # noqa: E501
                    text_impostos = " (IVA 21%, IE 3,8%)"
                fp_id = False  # tmp
                ctx.update({'force_fiscal_position': fp_id})
            pricelist['text_impostos'] = text_impostos

            # <% ctx['force_pricelist'] = polissa['pricelist'].id %>

            periodes_energia = sorted(pol.tarifa.get_periodes(context=context).keys())
            periodes_potencia = sorted(pol.tarifa.get_periodes('tp', context=context).keys())

            ctx['potencia_anual'] = True
            ctx['sense_agrupar'] = True
            power_prices = {}
            for p in periodes_potencia:
                power_prices[p] = get_atr_price(cursor, uid, pol, p, 'tp', ctx, with_taxes=True)[0]
            pricelist['power_prices'] = power_prices

            power_prices_untaxed = {}
            for p in periodes_potencia:
                power_prices_untaxed[p] = get_atr_price(
                    cursor, uid, pol, p, 'tp', ctx, with_taxes=False)[0]
            pricelist['power_prices_untaxed'] = power_prices_untaxed

            energy_prices = {}
            for p in periodes_energia:
                energy_prices[p] = get_atr_price(cursor, uid, pol, p, 'te', ctx, with_taxes=True)[0]
            pricelist['energy_prices'] = energy_prices

            energy_prices_untaxed = {}
            for p in periodes_energia:
                energy_prices_untaxed[p] = get_atr_price(
                    cursor, uid, pol, p, 'te', ctx, with_taxes=False)[0]
            pricelist['energy_prices_untaxed'] = energy_prices_untaxed

            generation_prices = {}
            for p in periodes_energia:
                generation_prices[p] = get_gkwh_atr_price(
                    cursor, uid, pol, p, ctx, with_taxes=True)[0]
            pricelist['generation_prices'] = generation_prices

            pricelist['price_auto'] = get_atr_price(
                cursor, uid, pol, periodes_energia[0], 'ac', ctx, with_taxes=True)[0]
            pricelist['price_auto_untaxed'] = get_atr_price(
                cursor, uid, pol, periodes_energia[0], 'ac', ctx, with_taxes=False)[0]
            res['pricelists'].append(pricelist)

        return res


ReportBackendCondicionsParticulars()


PuppeteerParser(
    'report.report_condicions_particulars',
    'report.backend.condicions.particulars',
    'som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako',
    params={}
)
