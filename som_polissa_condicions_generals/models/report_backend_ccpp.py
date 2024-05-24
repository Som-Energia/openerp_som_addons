# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import osv
from gestionatr.defs import TABLA_9
from giscedata_facturacio.report.utils import get_atr_price, get_comming_atr_price
from tools.translate import _


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


def clean_text(text):
    return text or ''


class ReportBackendCondicionsParticulars(ReportBackend):
    _source_model = "giscedata.polissa"
    _name = "report.backend.condicions.particulars"

    _decimals = {
        ('potencia', 'potencies_contractades'): 0,
    }

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        pol_o = self.pool.get("giscedata.polissa")
        pol_br = pol_o.browse(cursor, uid, record_id, context=context)

        return pol_br.titular.lang

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
            "fiscal_poisition": self.calculate_fiscal_position(cursor, uid, pol, context=context),
            # "prices": self.get_prices_data(cursor, uid, pol, context=context),
        }
        return data

    def get_titular_data(self, cursor, uid, pol, pas01, context=None):
        if context is None:
            context = {}

        res = {}
        if pas01:
            dades_client = pas01.pas_id.dades_client
            dades_envio = pas01.pas_id.direccio_notificacio
            es_ct_subrogacio = pas01.pas_id.sollicitudadm == "S" and pas01.pas_id.canvi_titular == "S"  # noqa: E501
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

        return res

    def get_potencies_data(self, cursor, uid, polissa, pas01, context=None):
        res = {}
        if pas01:
            es_canvi_tecnic = pas01.pas_id.sollicitudadm == "N"
        else:
            es_canvi_tecnic = False
        res['potencies'] = pas01.pas_id.pot_ids if es_canvi_tecnic else polissa.potencies_periode
        res['autoconsum'] = pas01.pas_id.tipus_autoconsum if es_canvi_tecnic else polissa.autoconsumo  # noqa: E501
        if res['autoconsum'] and res['autoconsum'] in TABLA_113_dict:
            res['autoconsum'] = TABLA_113_dict[res['autoconsum']]
        res['es_canvi_tecnic'] = es_canvi_tecnic
        res['periodes_energia'] = sorted(polissa.tarifa.get_periodes(context=context).keys())
        res['periodes_potencia'] = sorted(polissa.tarifa.get_periodes('tp', context=context).keys())

        return res

    def get_polissa_data(self, cursor, uid, pol, context=None):
        res = {}
        res['data_final'] = pol.modcontractual_activa.data_final or ''
        res['data_inici'] = pol.data_alta or ''
        res['name'] = pol.name
        res['state'] = pol.state
        res['lead'] = context.get('lead', False)
        res['pricelist'] = pol.llista_preu
        res['tarifa_provisional'] = context.get('tarifa_provisional', False)
        res['auto'] = pol.autoconsumo
        res['contract_type'] = pol.contract_type
        res['tarifa'] = pol.tarifa_codi
        res['data_baixa'] = pol.data_baixa
        res['fiscal_poisition'] = pol.fiscal_poisition
        res['potencia_max'] = pol.potencia
        res['mode_facturacio'] = pol.mode_facturacio
        res['coeficient_k'] = pol.coeficient_k
        res['coeficient_d'] = pol.coeficient_d
        res['te_assignacio_gkwh'] = pol.te_assignacio_gkwh
        res['bank'] = pol.bank
        res['printable_iban'] = pol.bank.printable_iban[5:]
        imd_obj = self.pool.get('ir.model.data')
        polissa_categ_obj = self.pool.get('giscedata.polissa.category')
        polissa_categ_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa', 'categ_tarifa_empresa'
        )[1]
        pol_categ = polissa_categ_obj.browse(cursor, uid, polissa_categ_id)
        if pol_categ in pol.category_id:
            res['is_business'] = True
        else:
            res['is_business'] = False
        # pol.pagador.name if not pas01 else dict_titular['client_name']
        if res['state'] != 'esborrany' and not res['lead']:
            res['last_modcon_state'] = pol.modcontractuals_ids[0].state
            res['last_modcon_facturacio'] = pol.modcontractuals_ids[0].mode_facturacio
            res['modcon_pendent_indexada'] = res['last_modcon_state'] == 'pendent' and res['last_modcon_facturacio'] == 'index'  # noqa: E501
            res['modcon_pendent_periodes'] = res['last_modcon_state'] == 'pendent' and res['last_modcon_facturacio'] == 'atr'  # noqa: E501
            res['last_modcon_pricelist'] = pol.modcontractuals_ids[0].llista_preu
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

    def calculate_fiscal_position(self, cursor, uid, pol, context=None):
        res = {}
        # lead = context.get('lead')
        # cfg_obj = self.pool.get('res.config')
        # omie_obj = self.pool.get('giscedata.monthly.price.omie')
        # iva_10_active = eval(cfg_obj.get(
        #     cursor, uid, 'charge_iva_10_percent_when_available', '0'
        # ))
        # start_date_iva_10 = cfg_obj.get(
        #     cursor, uid, 'charge_iva_10_percent_when_start_date', '2021-06-01'
        # )
        # end_date_iva_10 = cfg_obj.get(
        #     cursor, uid, 'iva_reduit_get_tariff_prices_end_date', '2024-12-31'
        # )
        # omie_mon_price_45 = omie_obj.has_to_charge_10_percent_requeriments_oficials(cursor, uid, context['date'], pol.potencia)  # noqa: E501
        # dades_tarifa = get_comming_atr_price(cursor, uid, pol, context)
        # if not pol.fiscal_position_id and not lead:
        #     imd_obj = self.pool.get('ir.model.data')
        #     if iva_10_active and pol.potencia <= 10 and dades_tarifa['date_start'] >= start_date_iva_10 and dades_tarifa['date_start'] <= end_date_iva_10 and omie_mon_price_45:  # noqa: E501
        #         fp_id = imd_obj.get_object_reference(cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]  # noqa: E501
        #         text_impostos = " (IVA 10%, IE 3,8%)"
        #     else:
        #         fp_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_iese', 'fp_nacional_2024_rdl_8_2023_38')[1]  # noqa: E501
        #         text_impostos = " (IVA 21%, IE 3,8%)"
        # res['fiscal_position'] = fp_id
        # res['text_impostos'] = text_impostos
        return res

    def get_prices_data(self, cursor, uid, pol, context=None):
        res = {}
        # lead = context.get('lead')
        # dict_preus_tp_potencia = False
        # dict_preus_tp_energia = False

        # if context.get('tarifa_provisional', False):
        #     dict_preus_tp_energia = context.get('tarifa_provisional')['preus_provisional_energia']
        #     if context.get('tarifa_provisional', False):
        #         if context['tarifa_provisional'].get('preus_provisional_potencia'):
        #             dict_preus_tp_potencia = context['tarifa_provisional']['preus_provisional_potencia']  # noqa: E501

        # res['tarifes_a_mostrar'] = get_comming_atr_price(cursor, uid, pol, context)
        return res


ReportBackendCondicionsParticulars()


PuppeteerParser(
    'report.report_condicions_particulars',
    'report.backend.condicions.particulars',
    'som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako',
    params={}
)
