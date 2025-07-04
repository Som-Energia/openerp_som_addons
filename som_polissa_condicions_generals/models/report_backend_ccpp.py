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
from som_polissa.giscedata_cups import TABLA_113_dict

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

        pol_obj = self.pool.get("giscedata.polissa")
        lang = pol_obj.browse(cursor, uid, record_id, context=context).titular.lang
        if context.get("lead") and context.get("lang"):
            lang = context.get("lang")
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
            pas_id = int(pas_id)
            pas = m101_obj.browse(cursor, uid, pas_id)
            dades_client = pas.dades_client
            dades_envio = pas.direccio_notificacio
            es_ct_subrogacio = pas.sollicitudadm == "S" and pas.canvi_titular == "S"
        else:
            dades_client = False
            dades_envio = False
            es_ct_subrogacio = False

        res['client_name'] = dades_client.name if es_ct_subrogacio and dades_client else pol.titular.name  # noqa: E501
        client_vat = dades_client.vat if es_ct_subrogacio and dades_client else pol.titular.vat  # noqa: E501
        res['client_vat'] = client_vat.replace('ES', '')
        direccio_titular = dades_client.address[0] if es_ct_subrogacio and dades_client else pol.titular.address[0]  # noqa: E501
        direccio_envio = dades_envio if es_ct_subrogacio and dades_envio else pol.direccio_notificacio  # noqa: E501
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
        res['lang'] = pol.titular.lang
        if context.get("lead") and context.get("lang"):
            res['lang'] = context.get("lang")

        return res

    def get_potencies_data(self, cursor, uid, pol, pas01, context=None):
        res = {}
        if pas01:
            m101_obj = self.pool.get("giscedata.switching.m1.01")
            pas_id = pas01.pas_id.split(",")[1]
            pas_id = int(pas_id)
            pas = m101_obj.browse(cursor, uid, pas_id)
            es_canvi_tecnic = pas.sollicitudadm == "N"
        else:
            es_canvi_tecnic = False
        pots = pas.pot_ids if es_canvi_tecnic else pol.potencies_periode
        res['autoconsum'] = pas.tipus_autoconsum if es_canvi_tecnic else pol.tipus_subseccio
        if res['autoconsum'] and res['autoconsum'] in TABLA_113_dict:
            res['autoconsum'] = TABLA_113_dict[res['autoconsum']]
        res['es_canvi_tecnic'] = es_canvi_tecnic
        periodes = []
        for i in range(0, 6):
            if i < len(pots):
                periode = pots[i].potencia
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
        res = {}
        res['data_final'] = pol.modcontractual_activa.data_final or ''
        res['data_inici'] = pol.data_alta or ''
        res['name'] = pol.name
        res['state'] = pol.state
        res['lead'] = context.get('lead', False)
        res['auto'] = pol.tipus_subseccio
        res['contract_type'] = CONTRACT_TYPES[pol.contract_type]
        res['tarifa'] = pol.tarifa_codi
        res['data_baixa'] = pol.data_baixa
        # res['fiscal_position'] = pol.fiscal_position
        res['potencia_max'] = pol.potencia
        res['mode_facturacio'] = pol.mode_facturacio

        res['te_assignacio_gkwh'] = pol.te_assignacio_gkwh
        res['bank'] = pol.bank or False
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
            res['modcon_pendent_auvi'] = False
        elif pol.state != 'esborrany' and not res['lead']:
            res['last_modcon_state'] = pol.modcontractuals_ids[0].state
            res['last_modcon_facturacio'] = pol.modcontractuals_ids[0].mode_facturacio
            res['last_modcon_auvi'] = pol.modcontractuals_ids[0].te_auvidi
            res['modcon_pendent_indexada'] = res['last_modcon_state'] == 'pendent' and res['last_modcon_facturacio'] == 'index'  # noqa: E501
            res['modcon_pendent_periodes'] = res['last_modcon_state'] == 'pendent' and res['last_modcon_facturacio'] == 'atr'  # noqa: E501
            res['modcon_pendent_auvi'] = res['last_modcon_state'] == 'pendent' and res['last_modcon_auvi']  # noqa: E501

        if res['modcon_pendent_indexada'] or res['modcon_pendent_periodes']:
            res['pricelist'] = pol.modcontractuals_ids[0].llista_preu
        elif pol.llista_preu:
            res['pricelist'] = pol.llista_preu
        else:
            tarifes_ids = llista_preu_o.search(cursor, uid, [])
            res['pricelist'] = pol_o.escull_llista_preus(
                cursor, uid, pol.id, tarifes_ids, context=context)

        if context.get('tarifa_provisional', False):
            res['tarifa_mostrar'] = 'Tarifa Períodes Empresa'
        else:
            res['tarifa_mostrar'] = res['pricelist'].nom_comercial or res['pricelist'].name

        if res['pricelist']:
            res['pricelist'] = res['pricelist'].id

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

    def get_mostra_auvi(self, cursor, uid, pol, context=None):
        res = False
        if pol.state == 'esborrany' and pol.te_auvidi:
            # Pol esborrany amb AUVI
            res = True
        elif pol.state != 'esborrany' and not context.get('lead', False):
            # Pol activa
            last_modcon_state = pol.modcontractuals_ids[0].state
            last_modcon_facturacio = pol.modcontractuals_ids[0].mode_facturacio
            last_modcon_auvi = pol.modcontractuals_ids[0].te_auvidi
            modcon_pendent_periodes = last_modcon_state == 'pendent' and last_modcon_facturacio == 'atr'  # noqa: E501
            modcon_pendent_auvi = last_modcon_state == 'pendent' and last_modcon_auvi
            modcon_pendent_quit_auvi = last_modcon_state == 'pendent' \
                and pol.te_auvidi and not pol.modcontractuals_ids[0].te_auvidi

            if (not pol.te_auvidi and not modcon_pendent_auvi) \
                    or (pol.te_auvidi and (modcon_pendent_periodes or modcon_pendent_quit_auvi)):
                res = False
            elif (pol.te_auvidi and not modcon_pendent_periodes and not modcon_pendent_quit_auvi) \
                    or modcon_pendent_auvi:
                res = True
        return res

    def get_pauvi(self, cursor, uid, sgpol, context, ctx):
        imd_obj = self.pool.get('ir.model.data')
        fp_obj = self.pool.get('account.fiscal.position')
        pricelist_index = sgpol.servei_generacio_id.llista_preu_venda_id
        if not pricelist_index:
            return 0.0

        fp_k_id = sgpol.polissa_id.fiscal_position_id \
            if sgpol.polissa_id.fiscal_position_id else ctx.get('force_fiscal_position', False)
        if fp_k_id:
            fp_k = fp_obj.browse(cursor, uid, fp_k_id)
        else:
            fp_k = False
        poduct_pauvi_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_auvi_som'
        )[1]

        pauvi = pricelist_index.get_atr_price(
            tipus='', product_id=poduct_pauvi_id, fiscal_position=fp_k,
            with_taxes=False)[0]
        return pauvi

    def get_auvi_data(self, cursor, uid, pol, context=None, ctx=None):
        res = {}
        sgpol_obj = self.pool.get('giscedata.servei.generacio.polissa')
        auvi = self.get_mostra_auvi(cursor, uid, pol, context=context)
        auvi_pauvi = 0.0
        auvi_name = ""
        auvi_percent = 0.0
        if self.get_mostra_auvi(cursor, uid, pol, context=context):
            today_str = datetime.today().strftime("%Y-%m-%d")
            sgpol_ids = sgpol_obj.search(cursor, uid, [
                ('polissa_id', '=', pol.id),
                ('cups_name', '=', pol.cups.name),
                '|',
                ('data_sortida', '=', False),
                ('data_sortida', '>', today_str),
                '|',
                '&',
                ('data_inici', '!=', False),
                ('data_inici', '<=', today_str),
                '&',
                ('data_inici', '=', False),
                ('data_incorporacio', '<=', today_str),
            ])
            if len(sgpol_ids) > 0:
                sgpol = sgpol_obj.browse(cursor, uid, sgpol_ids[0])
                auvi_percent = sgpol.percentatge or 0.0
                auvi_name = sgpol.servei_generacio_id.name
                auvi_pauvi = self.get_pauvi(cursor, uid, sgpol, context, ctx)

        res = {
            'auvi': auvi,
            'auvi_pauvi': auvi_pauvi,
            'auvi_name': auvi_name,
            'auvi_percent': auvi_percent,
        }
        return res

    def get_prices_data(self, cursor, uid, pol, context=None):  # noqa: C901
        res = {}
        lead = context.get('lead')
        dict_preus_tp_potencia = False
        dict_preus_tp_energia = False
        omie_obj = self.pool.get('giscedata.monthly.price.omie')
        pol_obj = self.pool.get('giscedata.polissa')
        cfg_obj = self.pool.get('res.config')
        imd_obj = self.pool.get('ir.model.data')
        prod_obj = self.pool.get("product.product")
        pricelist_obj = self.pool.get('product.pricelist')
        fp_obj = self.pool.get('account.fiscal.position')
        polissa = pol_obj.browse(cursor, uid, pol.id)
        if context.get('tarifa_provisional', False):
            dict_preus_tp_energia = context.get('tarifa_provisional')['preus_provisional_energia']
            if context.get('tarifa_provisional', False):
                if context['tarifa_provisional'].get('preus_provisional_potencia'):
                    dict_preus_tp_potencia = context['tarifa_provisional']['preus_provisional_potencia']  # noqa: E501

        res['dict_preus_tp_energia'] = dict_preus_tp_energia
        res['dict_preus_tp_potencia'] = dict_preus_tp_potencia

        ctx = {'date': datetime.today()}
        modcon_pendent_indexada = False
        modcon_pendent_periodes = False
        if pol.state != 'esborrany':
            ultima_modcon = pol.modcontractuals_ids[0]
            modcon_pendent_indexada = ultima_modcon.state == 'pendent' and \
                ultima_modcon.mode_facturacio == 'index'
            modcon_pendent_periodes = ultima_modcon.state == 'pendent' and \
                ultima_modcon.mode_facturacio == 'atr'
            if modcon_pendent_indexada or modcon_pendent_periodes:
                ctx.update({'force_pricelist': pol.modcontractuals_ids[0].llista_preu.id})
        if polissa.data_baixa:
            ctx = {'date': datetime.strptime(polissa.data_baixa, '%Y-%m-%d')}
        if not pol.llista_preu:
            tarifes_a_mostrar = []
            if dict_preus_tp_potencia:
                tarifes_a_mostrar = [dict_preus_tp_potencia]
        else:
            tarifes_a_mostrar = get_comming_atr_price(cursor, uid, polissa, ctx)
        tarifes_a_mostrar if isinstance(tarifes_a_mostrar, list) else [tarifes_a_mostrar]
        if polissa.state == 'esborrany' and not polissa.llista_preu:
            tarifes_ids = pricelist_obj.search(cursor, uid, [])
            pricelist_id = pol_obj.escull_llista_preus(
                cursor, uid, pol.id, tarifes_ids, context=context)
            ctx.update({'force_pricelist': pricelist_id.id})
            tarifes_a_mostrar = get_comming_atr_price(cursor, uid, polissa, ctx)
        res['pricelists'] = []
        for dades_tarifa in tarifes_a_mostrar:
            text_vigencia = ''
            pricelist = {}

            if lead:
                text_vigencia = ''
            elif (not pol.modcontractual_activa.data_final and not (modcon_pendent_indexada or modcon_pendent_indexada)) and dades_tarifa['date_end']:  # noqa: E501
                text_vigencia = _(u"(vigents fins al {})").format(
                    datetime.strptime(dades_tarifa['date_end'], '%Y-%m-%d').strftime('%d/%m/%Y'))
            elif dades_tarifa['date_end'] and dades_tarifa['date_start']:
                text_vigencia = _(u"(vigents fins al {})").format(
                    (datetime.strptime(dades_tarifa['date_end'], '%Y-%m-%d')).strftime('%d/%m/%Y'))
            elif dades_tarifa['date_start'] and datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d') > datetime.today():  # noqa: E501
                text_vigencia = _(u"(vigents a partir del {})").format(
                    datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d').strftime('%d/%m/%Y'))
                ctx.update({'date': datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d')})
            pricelist['text_vigencia'] = text_vigencia

            try:
                omie_mon_price_45 = omie_obj.has_to_charge_10_percent_requeriments_oficials(
                    cursor, uid, datetime.strftime(datetime.today(), "%Y-%m-%d"), pol.potencia)
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
                    fp_id = imd_obj.get_object_reference(
                        cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
                    text_impostos = " (IVA 10%, IE 5,11%)"
                    ctx.update({'force_fiscal_position': fp_id})
                else:
                    text_impostos = " (IVA 21%, IE 5,11%)"

            pricelist['text_impostos'] = text_impostos

            periodes_energia = sorted(pol.tarifa.get_periodes(context=context).keys())
            periodes_potencia = sorted(pol.tarifa.get_periodes('tp', context=context).keys())

            ctx['potencia_anual'] = True
            ctx['sense_agrupar'] = True
            ctx['pricelist_base_price'] = 0.0  # Dummy base price to avoid error
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

            generation_prices_untaxed = {}
            for p in periodes_energia:
                generation_prices_untaxed[p] = get_gkwh_atr_price(
                    cursor, uid, pol, p, ctx, with_taxes=False)[0]
            pricelist['generation_prices_untaxed'] = generation_prices_untaxed

            pricelist['price_auto'] = get_atr_price(
                cursor, uid, pol, periodes_energia[0], 'ac', ctx, with_taxes=True)[0]
            pricelist['price_auto_untaxed'] = get_atr_price(
                cursor, uid, pol, periodes_energia[0], 'ac', ctx, with_taxes=False)[0]

            res['pricelists'].append(pricelist)

        coeficient_k_untaxed = (pol.coeficient_k + pol.coeficient_d) / 1000
        coeficient_k = False
        res['mostra_indexada'] = False
        fp_k_id = polissa.fiscal_position_id.id if pol.fiscal_position_id else ctx.get(
            'force_fiscal_position', False)
        if fp_k_id:
            fp_k = fp_obj.browse(cursor, uid, fp_k_id)
        else:
            fp_k = False
        coeficient_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada', 'product_factor_k'
        )[1]
        if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:  # noqa: E501
            res['mostra_indexada'] = True
            if coeficient_k_untaxed == 0:
                if modcon_pendent_indexada:
                    pricelist_index = pol.modcontractuals_ids[0].llista_preu
                elif pol.llista_preu:
                    pricelist_index = pol.llista_preu
                else:
                    tarifes_ids = pricelist_obj.search(cursor, uid, [])
                    pricelist_index = pol_obj.escull_llista_preus(
                        cursor, uid, pol.id, tarifes_ids, context=context)
                coeficient_k_untaxed = pricelist_index.get_atr_price(
                    tipus='', product_id=coeficient_id, fiscal_position=fp_k,
                    with_taxes=False)[0]
                coeficient_k = pricelist_index.get_atr_price(
                    tipus='', product_id=coeficient_id, fiscal_position=fp_k,
                    with_taxes=True)[0]
            else:
                coeficient_k = prod_obj.add_taxes(
                    cursor, uid, coeficient_id, coeficient_k_untaxed, fp_k,
                    direccio_pagament=polissa.direccio_pagament, titular=polissa.titular,
                    context=context,
                )
        res['coeficient_k_untaxed'] = coeficient_k_untaxed
        res['coeficient_k'] = coeficient_k

        # AUVI
        auvi_data = self.get_auvi_data(cursor, uid, pol, context, ctx)
        res.update(auvi_data)

        return res


ReportBackendCondicionsParticulars()


PuppeteerParser(
    'report.report_condicions_particulars',
    'report.backend.condicions.particulars',
    'som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako',
    params={}
)
