## -*- encoding: utf-8 -*-
<%
import calendar
import time, babel
from datetime import datetime
from giscedata_facturacio.report.utils import get_atr_price, get_comming_atr_price
from som_extend_facturacio_comer.utils import get_gkwh_atr_price
from giscedata_polissa.report.utils import localize_period, datetime_to_date
from gestionatr.defs import TABLA_9

lead = context.get('lead')

dict_preus_tp_potencia = False
dict_preus_tp_energia = False

if context.get('tarifa_provisional', False):
    dict_preus_tp_energia = context.get('tarifa_provisional')['preus_provisional_energia']
    if context.get('tarifa_provisional', False):
        if context['tarifa_provisional'].get('preus_provisional_potencia'):
            dict_preus_tp_potencia = context['tarifa_provisional']['preus_provisional_potencia']


def clean_text(text):
    return text or ''

def get_pas01(cas):
    for step_id in cas.step_ids:
        proces_name = step_id.proces_id.name
        step_name = step_id.step_id.name
        if proces_name == "M1" and step_name == "01":
            return step_id
    return None

def get_titular_data(pas01, polissa):
    res = {}
    if pas01:
        dades_client = pas01.pas_id.dades_client
        dades_envio = pas01.pas_id.direccio_notificacio
        es_ct_subrogacio = pas01.pas_id.sollicitudadm == "S" and pas01.pas_id.canvi_titular == "S"
    else:
        dades_client = False
        dades_envio = False
        es_ct_subrogacio = False

    res['client_name'] = dades_client.name if es_ct_subrogacio and dades_client else polissa.titular.name
    res['client_vat'] = dades_client.vat if es_ct_subrogacio and dades_client else polissa.titular.vat
    res['direccio_titular'] = dades_client.address[0] if es_ct_subrogacio and dades_client else polissa.titular.address[0]
    res['direccio_envio'] =  dades_envio if es_ct_subrogacio and dades_envio else polissa.direccio_notificacio
    res['diferent'] = (res['direccio_envio'] != res['direccio_titular'])
    return res

TABLA_113_dict = { # Table extracted from gestionatr.defs TABLA_113, not imported due translations issues
    '00': _(u"Sense Autoconsum"), # Sin Autoconsumo
    '01': _(u"Autoconsum Tipus 1"), # Autoconsumo Tipo 1
    '2A': _(u"Autoconsum tipus 2 (segons l'Art. 13. 2. a) RD 900/2015)"), # Autoconsumo tipo 2 (según el Art. 13. 2. a) RD 900/2015)
    '2B': _(u"Autoconsum tipus 2 (segons l'Art. 13. 2. b) RD 900/2015)"), # Autoconsumo tipo 2 (según el Art. 13. 2. b) RD 900/2015)
    '2G': _(u"Serveis auxiliars de generació lligada a un autoconsum tipus 2"), # Servicios auxiliares de generación ligada a un autoconsumo tipo 2
    '31': _(u"Sense Excedents Individual - Consum"), # Sin Excedentes Individual – Consumo
    '32': _(u"Sense Excedents Col·lectiu - Consum"), # Sin Excedentes Colectivo – Consumo
    '33': _(u"Sense Excedents Col·lectiu amb acord de compensació – Consum"), # Sin Excedentes Colectivo con acuerdo de compensación – Consumo
    '41': _(u"Amb excedents i compensació Individual-Consum"), # Con excedentes y compensación Individual - Consumo 
    '42': _(u"Amb excedents i compensació Col·lectiu-Consum"), # Con excedentes y compensación Colectivo– Consumo
    '43': _(u"Amb excedents i compensació Col·lectiu a través de xarxa - Consum"), # Con excedentes y compensación Colectivo a través de red - Consumo
    '51': _(u"Amb excedents sense compensació Individual sense cte. de Serv. Aux. en Xarxa Interior - Consum"), # Con excedentes sin compensación Individual sin cto de SSAA en Red Interior– Consumo
    '52': _(u"Amb excedents sense compensació Col·lectiu sense cte. de Serv. Aux. en Xarxa Interior - Consum"), # Con excedentes sin compensación Colectivo sin cto de SSAA en Red Interior– Consumo
    '53': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. en Xarxa Interior - Consum"), # Con excedentes sin compensación Individual con cto SSAA en Red Interior– Consumo
    '54': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. en Xarxa Interior - Serv. Aux."), # Con excedentes sin compensación individual con cto SSAA en Red Interior– SSAA
    '55': _(u"Amb excedents sense compensació Col·lectiu / en Xarxa Interior - Consum"), # Con excedentes sin compensación Colectivo/en Red Interior– Consumo
    '56': _(u"Amb excedents sense compensació Col·lectiu / en Xarxa Interior - Serv. Aux."), # Con excedentes sin compensación Colectivo/en Red Interior - SSAA
    '61': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. a través de xarxa - Consum"), # Con excedentes sin compensación Individual con cto SSAA a través de red – Consumo
    '62': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. a través de xarxa - Serv. Aux."), # Con excedentes sin compensación individual con cto SSAA a través de red – SSAA
    '63': _(u"Amb excedents sense compensació Col·lectiu a través de xarxa - Consum"), # Con excedentes sin compensación Colectivo a través de red – Consumo
    '64': _(u"Amb excedents sense compensació Col·lectiu a través de xarxa - Serv. Aux."), # Con excedentes sin compensación Colectivo a través de red - SSAA
    '71': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Consum"), # Con excedentes sin compensación Individual con cto SSAA a través de red y red interior – Consumo
    '72': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Serv. Aux."), # Con excedentes sin compensación individual con cto SSAA a través de red y red interior – SSAA
    '73': _(u"Amb excedents sense compensació Col·lectiu amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Consum"), # Con excedentes sin compensación Colectivo con cto de SSAA  a través de red y red interior – Consumo
    '74': _(u"Amb excedents sense compensació Col·lectiu amb cte. de Serv. Aux. a través de xarxa i xarxa interior - SSAA"), # Con excedentes sin compensación Colectivo con cto de SSAA a través de red y red interior - SSAA
    }

def get_potencies(pas01, polissa):
    res = {}
    if pas01:
        es_canvi_tecnic = pas01.pas_id.sollicitudadm == "N"
    else:
        es_canvi_tecnic = False
    res['potencies'] = pas01.pas_id.pot_ids if es_canvi_tecnic else polissa.potencies_periode
    res['autoconsum'] = pas01.pas_id.tipus_autoconsum if es_canvi_tecnic else polissa.autoconsumo
    if res['autoconsum'] and res['autoconsum'] in TABLA_113_dict:
            res['autoconsum'] = TABLA_113_dict[res['autoconsum']]
    res['es_canvi_tecnic'] = es_canvi_tecnic
    return res

CONTRACT_TYPES = dict(TABLA_9)

%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
    <style>
        @font-face {
            font-family: "Roboto";
            src: url("${assets_path}/fonts/Roboto/Roboto-Regular.ttf") format('truetype');
            font-weight: normal;
        }
        @font-face {
            font-family: "Roboto";
            src: url("${assets_path}/fonts/Roboto/Roboto-Bold.ttf") format('truetype');
            font-weight: bold;
        }
        @font-face {
            font-family: "Roboto";
            src: url("${assets_path}/fonts/Roboto/Roboto-Thin.ttf") format('truetype');
            font-weight: 200;
        }
    </style>
    <style type="text/css">
        ${css}
    </style>
    <link rel="stylesheet" href="${addons_path}/som_polissa_condicions_generals/report/condicions_particulars.css"/>
</head>
<body>
    <%def name="clean(text)">
        ${text or ''}
    </%def>
    <%def name="enviament(diferent, text)">
        %if diferent:
            ${clean(text)}
        %endif
    </%def>
    %for obj in objects:
        <%
            if obj._name == 'giscedata.switching':
                pol_obj = obj.pool.get('giscedata.polissa')
                polissa = pol_obj.browse(cursor, uid, obj.cups_polissa_id.id)
                pas01 = get_pas01(obj)
            elif obj._name == 'giscedata.polissa':
                polissa = obj
                pas01 = False
            lang = polissa.titular.lang
            if lang not in ['ca_ES', 'es_ES']:
                lang = 'es_ES'
            setLang(lang)
        %>
        <div id="capcelera">
            <div id="logo_capcelera">
                <img id="logo" src="${addons_path}/som_polissa_condicions_generals/report/assets/logo.png"/>
            </div>
            <div id="address_capcelera">
                <b>${_(u"Som Energia, SCCL")}</b><br/>
                <b>${_(u"CIF:")}</b> ${_(u" F55091367")}<br/>
                <b>${_(u"Domicili:")}</b> ${_(u" C/Pic de Peguera, 9 (1a planta)<br/>17003, Girona")}<br/>
                <b>${_(u"Adreça electrònica:")} </b> ${_(u" info@somenergia.coop")}
            </div>
            <div id="dades_capcelera">
                <div id="titol_dades">
                    <h3>${_(u"DADES DEL CONTRACTE")}</h3>
                </div>
                <div id="bloc_dades_capcelera">
                    <%
                        data_final = polissa.modcontractual_activa.data_final or ''
                        data_inici = polissa.data_alta or ''
                    %>
                    <b>${_(u"Contracte núm.: ")}</b> ${polissa.name}<br/>
                    <b>${_(u"Data d'inici del subministrament: ")}</b>
                    %if polissa.state == 'esborrany':
                        &nbsp;
                    %else:
                        ${data_inici}
                    %endif
                    <br/>
                    <b>${_(u"Data de renovació del subministrament: ")}</b>
                    %if polissa.state == 'esborrany':
                        &nbsp;
                    %else:
                        ${data_final}
                    %endif
                    <br/>
                </div>
            </div>
        </div>
        <div id="titol">
            <h2>${_(u"CONDICIONS PARTICULARS DEL CONTRACTE DE SUBMINISTRAMENT D'ENERGIA ELÈCTRICA")}</h2>
        </div>

        %if polissa.state == 'esborrany' and not lead:
            <div class="esborrany_warning">
                <img src="${addons_path}/som_polissa_condicions_generals/report/assets/warning_icon.png"/>
                <h2>
                    ${_("LES DADES D'AQUEST CONTRACTE ESTAN PENDENTS DE VALIDACIÓ.")}
                </h2>
                <h3>
                    ${_(u"Tarifes vigents en el moment d’activació del contracte.")}
                </h3>
            </div>
        %endif
        <%
            if polissa.state == 'esborrany':
                ultima_modcon = None
                modcon_pendent_indexada = False
                modcon_pendent_periodes = False

            dict_titular = get_titular_data(pas01, polissa)
            periodes_energia, periodes_potencia = [], []
            if polissa.state != 'esborrany':
                ultima_modcon = polissa.modcontractuals_ids[0]
                modcon_pendent_indexada = ultima_modcon.state == 'pendent' and ultima_modcon.mode_facturacio == 'index'
                modcon_pendent_periodes = ultima_modcon.state == 'pendent' and ultima_modcon.mode_facturacio == 'atr'
        %>
        <div class="contact_info">
            <div class="persona_titular styled_box ${"width33" if dict_titular['diferent'] else "width49"}">
                <h5>${_("PERSONA TITULAR")}</h5>
                <div class="inside_styled_box">
                    <b>${_(u"Nom/Raó social: ")}</b>
                    ${dict_titular['client_name']}<br/>
                    <b>${_(u"NIF/CIF: ")}</b>
                    ${dict_titular['client_vat'].replace('ES', '')}<br/>
                    <b>${_(u"Adreça: ")}</b>
                    ${clean(dict_titular['direccio_titular'].street)}<br/>
                    <b>${_(u"Codi postal i municipi: ")}</b>
                    ${clean(dict_titular['direccio_titular'].zip)} ${clean(dict_titular['direccio_titular'].city)}<br/>
                    <b>${_(u"Província i país: ")}</b>
                    ${clean(dict_titular['direccio_titular'].state_id.name)} ${clean(dict_titular['direccio_titular'].country_id.name)}<br/>
                    <b>${_(u"Adreça electrònica: ")}</b>
                    ${clean(dict_titular['direccio_titular'].email)}<br/>
                    <b>${_(u"Telèfon: ")}</b>
                    ${clean(dict_titular['direccio_titular'].mobile)}<br/>
                    <b>${_(u"Telèfon 2: ")}</b>
                    ${clean(dict_titular['direccio_titular'].phone)}<br/>
                </div>
            </div>

            <div class="dades_subministrament styled_box ${"width33" if dict_titular['diferent'] else "width49"}">
                <h5> ${_("DADES DEL PUNT DE SUBMINISTRAMENT")} </h5>

                <div class="inside_styled_box">
                    <b>${_(u"Adreça: ")}</b>
                    ${polissa.cups.direccio}</br>
                    <b>${_(u"Província i país: ")}</b>
                    ${polissa.cups.id_provincia.name} ${polissa.cups.id_provincia.country_id.name}</br>
                    <b>${_(u"CUPS: ")}</b>
                    ${polissa.cups.name}</br>
                    <b>${_(u"CNAE: ")}</b>
                    ${polissa.cnae.name}</br>
                    <b>${_(u"Contracte d'accés: ")}</b>
                    ${clean(polissa.ref_dist)}</br>
                    <b>${_(u"Activitat principal: ")}</b>
                    ${polissa.cnae.descripcio}</br>
                    <b>${_(u"Empresa distribuïdora: ")}</b>
                    ${polissa.cups.distribuidora_id.name}</br>
                    <b>${_(u"Tensió Nominal (V): ")}</b>
                    ${clean(polissa.tensio)}</br>
                </div>
            </div>

            %if dict_titular['diferent']:
            <div class="dades_de_contacte styled_box ${"width33" if dict_titular['diferent'] else "width49"}">
                <h5> ${_("DADES DE CONTACTE")} </h5>
                <div class="inside_styled_box">
                    <b>${_(u"Nom/Raó social: ")}</b>
                    ${enviament(dict_titular['diferent'], dict_titular['direccio_envio'].name)}<br/>
                    <b>${_(u"Adreça: ")}</b>
                    ${enviament(dict_titular['diferent'], dict_titular['direccio_envio'].street)}<br/>
                    <b>${_(u"Codi postal i municipi: ")}</b>
                    ${enviament(dict_titular['diferent'],
                        '{0} {1}'.format(
                            clean_text(dict_titular['direccio_envio'].zip), clean_text(dict_titular['direccio_envio'].city)
                        )
                    )}<br/>
                    <b>${_(u"Província i país: ")}</b>
                    ${enviament(dict_titular['diferent'],
                        '{0} {1}'.format(
                            clean_text(dict_titular['direccio_envio'].state_id.name), clean_text(dict_titular['direccio_envio'].country_id.name)
                        )
                    )}<br/>
                    <b>${_(u"Adreça electrònica: ")}</b>
                    ${enviament(dict_titular['diferent'],
                        '{0}'.format(
                            clean_text(dict_titular['direccio_envio'].email)
                        )
                    )}<br/>
                    <b>${_(u"Telèfon: ")}</b>
                    ${enviament(dict_titular['diferent'],
                        '{0}'.format(
                            clean_text(dict_titular['direccio_envio'].mobile)
                        )
                    )}<br/>
                    <b>${_(u"Telèfon 2: ")}</b>
                    ${enviament(dict_titular['diferent'],
                        '{0}'.format(
                            clean_text(dict_titular['direccio_envio'].phone)
                        )
                    )}<br/>
                </div>
            </div>
            %endif
        </div>

        <div class="peatge_acces styled_box">
            <h5> ${_("PEATGE I CÀRRECS (definits a la Circular de la CNMC 3/2020 i al Reial decret 148/2021)")} </h5>
            <%
                pol_o = pool.get('giscedata.polissa')
                llista_preu_o = pool.get('product.pricelist')
                dict_pot = get_potencies(pas01, polissa)
                ctx = {'lang': lang}

                if modcon_pendent_indexada or modcon_pendent_periodes:
                    llista_preus = ultima_modcon.llista_preu
                elif polissa.llista_preu:
                    llista_preus = polissa.llista_preu
                else:
                    tarifes_ids = llista_preu_o.search(cursor, uid, [])
                    llista_preus = pol_o.escull_llista_preus(cursor, uid, polissa.id, tarifes_ids, context=ctx)
                if context.get('tarifa_provisional', False):
                    tarifa_a_mostrar = 'Tarifa Períodes Empresa'
                else:
                    tarifa_a_mostrar = llista_preus.nom_comercial or llista_preus.name
            %>
            <div class="peatge_access_content">
                <div class="padding_left"><b>${_(u"Peatge de transport i distribució: ")}</b>${clean(polissa.tarifa_codi)}</div>
                <div class="padding_left"><b>${_(u"Tipus de contracte: ")}</b> ${CONTRACT_TYPES[polissa.contract_type]} ${"({0})".format(dict_pot['autoconsum']) if polissa.autoconsumo != '00' else ""}</div>
                <div class="padding_bottom padding_left"><b>${_(u"Tarifa: ")}</b> ${clean(tarifa_a_mostrar)}</div>
                <table class="taula_custom new_taula_custom">
                    <tr style="background-color: #878787;">
                        <th></th>
                        % if polissa.tarifa_codi == "2.0TD":
                            <th>${_(u"Punta")}</th>
                            <th></th>
                            <th>${_(u"Vall")}</th>
                            <th></th>
                            <th></th>
                            <th></th>
                        % else:
                            <th>P1</th>
                            <th>P2</th>
                            <th>P3</th>
                            <th>P4</th>
                            <th>P5</th>
                            <th>P6</th>
                        % endif
                    </tr>
                    <tr>
                        <td class="bold">${_(u"Potència contractada (kW):")}</td>
                        <%
                            potencies = dict_pot['potencies']
                            periodes = []
                            for i in range(0, 6):
                                if i < len(potencies):
                                    periode = potencies[i]
                                else:
                                    periode = False
                                periodes.append((i+1, periode))

                            if polissa.tarifa_codi == "2.0TD":
                                periodes[2] = periodes[1]
                                periodes[1] = False
                        %>
                        %if polissa.tarifa_codi == "2.0TD":
                            <td class="center">
                            %if periodes[0][1] and periodes[0][1].potencia:
                                <span>${formatLang(periodes[0][1].potencia / 1000.0 if dict_pot['es_canvi_tecnic'] else periodes[0][1].potencia, digits=3)}</span>
                            %endif
                            </td>
                            <td></td>
                            <td class="center">
                            %if periodes[2][1] and periodes[2][1].potencia:
                                <span>${formatLang(periodes[2][1].potencia / 1000.0 if dict_pot['es_canvi_tecnic'] else periodes[2][1].potencia, digits=3)}</span>
                            %endif
                            </td>
                        %else:
                            %for p in periodes:
                                <td class="center">
                                %if p[1] and p[1].potencia:
                                    <span>${formatLang(p[1].potencia / 1000.0 if dict_pot['es_canvi_tecnic'] else p[1].potencia, digits=3)}</span>
                                %endif
                                </td>
                            %endfor
                        %endif
                        %if len(periodes) < 6:
                            %for p in range(0, 6-len(periodes)):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %endif
                    </tr>
                </table>
            </div>
        </div>
        <%
            ctx = {'date': datetime.today()}
            if polissa.data_baixa:
                ctx = {'date': datetime.strptime(polissa.data_baixa, '%Y-%m-%d')}
            if not polissa.llista_preu:
                tarifes_a_mostrar = []
                if lead and dict_preus_tp_potencia:
                    tarifes_a_mostrar = [dict_preus_tp_potencia]
            else:
                tarifes_a_mostrar = get_comming_atr_price(cursor, uid, polissa, ctx)
            text_vigencia = ''

            cfg_obj = polissa.pool.get('res.config')
            start_date_mecanisme_ajust_gas = cfg_obj.get(
            cursor, uid, 'start_date_mecanisme_ajust_gas', '2022-10-01'
            )
            end_date_mecanisme_ajust_gas = cfg_obj.get(
                cursor, uid, 'end_date_mecanisme_ajust_gas', '2023-12-31'
            )

            start_date_iva_10 = cfg_obj.get(
                cursor, uid, 'charge_iva_10_percent_when_start_date', '2021-06-01'
            )
            end_date_iva_10 = cfg_obj.get(
                cursor, uid, 'iva_reduit_get_tariff_prices_end_date', '2024-12-31'
            )
            iva_10_active = eval(cfg_obj.get(
                cursor, uid, 'charge_iva_10_percent_when_available', '0'
            ))

        %>
        <div class="styled_box">
        %for dades_tarifa in tarifes_a_mostrar:
            <%
                if modcon_pendent_indexada or modcon_pendent_periodes or lead:
                    text_vigencia = ''
                elif not data_final and dades_tarifa['date_end']:
                    text_vigencia = _(u"(vigents fins al {})").format(dades_tarifa['date_end'])
                elif dades_tarifa['date_end'] and dades_tarifa['date_start']:
                    text_vigencia = _(u"(vigents fins al {})").format((datetime.strptime(dades_tarifa['date_end'], '%Y-%m-%d')).strftime('%d/%m/%Y'))
                elif datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d') > datetime.today():
                    text_vigencia = _(u"(vigents a partir del {})").format(datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d').strftime('%d/%m/%Y'))

                iva_reduit = False
                if not polissa.fiscal_position_id and not lead:
                    imd_obj = polissa.pool.get('ir.model.data')
                    if iva_10_active and polissa.potencia <= 10 and dades_tarifa['date_start'] >= start_date_iva_10 and dades_tarifa['date_start'] <= end_date_iva_10:
                        fp_id = imd_obj.get_object_reference(cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
                        iva_reduit = True
                        text_vigencia += " (IVA 10%, IE 2,5%)"
                    else:
                        fp_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_iese', 'fp_nacional_2024_rdl_8_2023_25')[1]
                        text_vigencia += " (IVA 21%, IE 2,5%)"
                    ctx.update({'force_fiscal_position': fp_id})
            %>
            %if text_vigencia:
                <h5> ${_("TARIFES D'ELECTRICITAT")} ${text_vigencia}</h5>
            %else:
                <h5> ${_("TARIFES D'ELECTRICITAT")}</h5>
            %endif
            <%
                periodes_potencia = []
                potencies = polissa.potencies_periode
                if potencies:
                    periodes = []
                    for i in range(0, 6):
                        if i < len(potencies):
                            periode = potencies[i]
                        else:
                            periode = False
                        periodes.append((i+1, periode))
                if potencies:
                    ctx['potencia_anual'] = True
                    ctx['sense_agrupar'] = True
                    periodes_energia = sorted(polissa.tarifa.get_periodes(context=ctx).keys())
                    periodes_potencia = sorted(polissa.tarifa.get_periodes('tp', context=ctx).keys())
                    if periodes and not lead:
                        if data_final: #TODO: A LA SEGONA PASSADA, POSARIEM ELS PREUS VELLS
                            data_llista_preus = dades_tarifa['date_start']
                            if datetime.strptime(data_llista_preus, '%Y-%m-%d') <= datetime.today():
                                data_llista_preus = min(datetime.strptime(data_final, '%Y-%m-%d'), datetime.today())
                            ctx['date'] = data_llista_preus
                        if not lead:
                            data_i = data_inici and datetime.strptime(polissa.modcontractual_activa.data_inici, '%Y-%m-%d')
                        else:
                            data_i = datetime.strptime(data_inici, '%Y-%m-%d')
                        if data_i and calendar.isleap(data_i.year):
                            dies = 366
                        else:
                            dies = 365
            %>
            <div class="tarifes_electricitat">
                <table class="taula_custom new_taula_custom">
                    <tr style="background-color: #878787;">
                        <th></th>
                        % if polissa.tarifa_codi == "2.0TD":
                            <th>${_(u"Punta")}</th>
                            <th></th>
                            <th>${_(u"Vall")}</th>
                            <th></th>
                            <th></th>
                            <th></th>
                        % else:
                            <th>P1</th>
                            <th>P2</th>
                            <th>P3</th>
                            <th>P4</th>
                            <th>P5</th>
                            <th>P6</th>
                        % endif
                    </tr>
                    <tr>
                        <td class="bold">${_("Terme potència (€/kW i any)")}</td>
                        %if polissa.tarifa_codi == "2.0TD":
                            %if polissa.llista_preu:
                                <td class="center">
                                    <span>${formatLang(get_atr_price(cursor, uid, polissa, periodes_potencia[0], 'tp', ctx, with_taxes=True)[0], digits=6)}</span>
                                </td>
                                <td></td>
                                <td class="center">
                                    <span>${formatLang(get_atr_price(cursor, uid, polissa, periodes_potencia[1], 'tp', ctx, with_taxes=True)[0], digits=6)}</span>
                                </td>
                                %for p in range(0, 3):
                                    <td class="">
                                        &nbsp;
                                    </td>
                                %endfor
                            %else:
                                %for p in range(0, 6):
                                    <td class="">
                                        &nbsp;
                                    </td>
                                %endfor
                            %endif
                        %else:
                            %for p in periodes_potencia:
                                %if polissa.llista_preu:
                                    <td class="center">
                                        <span><span>${formatLang(get_atr_price(cursor, uid, polissa, p, 'tp', ctx, with_taxes=True)[0], digits=6)}</span></span>
                                    </td>
                                %else:
                                    %if lead:
                                        <td class="center">
                                            <span><span>${formatLang(dict_preus_tp_potencia[p], digits=6)}</span></span>
                                        </td>
                                    %else:
                                        <td class="">
                                            &nbsp;
                                        </td>
                                    %endif
                                %endif
                            %endfor
                            %if len(periodes_potencia) < 6:
                                %for p in range(0, 6-len(periodes_potencia)):
                                    <td class="">
                                        &nbsp;
                                    </td>
                                %endfor
                            %endif
                        %endif
                    </tr>

                    % if polissa.tarifa_codi == "2.0TD":
		        </table>
                <table class="taula_custom doble_table new_taula_custom">
                    <tr style="background-color: #878787;">
                            <th></th>
                            <th>${_(u"Punta")}</th>
                            <th>${_(u"Pla")}</th>
                            <th>${_(u"Vall")}</th>
                            <th></th>
                            <th></th>
                            <th></th>
                    </tr>
                    %endif
                    <tr>
                        <td class="bold">${_("Terme energia (€/kWh)")}</td>
                        %if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:
                            <td class="center reset_line_height" colspan="6">
                                <span class="normal_font_weight">
                                    <b>${_(u"Tarifa indexada")}</b>${_(u"(2) - el preu horari (PH) es calcula d'acord amb la fórmula:")}
                                </span>
                                <br/>
                                <span>${_(u"PH = 1,015 * [(PHM + PHMA + Pc + Sc + I + POsOm) (1 + Perd) + FE + F] + PTD + CA")}</span>
                                <br/>
                                <span class="normal_font_weight">${_(u"on la franja de la cooperativa")}</span>
                                <%
                                    coeficient_k = (polissa.coeficient_k + polissa.coeficient_d)/1000
                                    if coeficient_k == 0:
                                        today = datetime.today().strftime("%Y-%m-%d")
                                        vlp = None
                                        if modcon_pendent_indexada:
                                            llista_preus = ultima_modcon.llista_preu.version_id
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
                                %>
                                <span>&nbsp;${("(F) = %s €/kWh</B>") % formatLang(coeficient_k, digits=6)}</span>
                            </td>
                        %else:
                            <% llista_preu = ultima_modcon.llista_preu if modcon_pendent_periodes else polissa.llista_preu %>
                            %for p in periodes_energia:
                                %if llista_preu and not lead:
                                    <% ctx['force_pricelist'] = llista_preu.id %>
                                    <td class="center">
                                        <span class="">${formatLang(get_atr_price(cursor, uid, polissa, p, 'te', ctx, with_taxes=True)[0], digits=6)}</span>
                                    </td>
                                %else:
                                    %if lead:
                                        <td class="center">
                                            <span><span>${formatLang(dict_preus_tp_energia[p], digits=6)}</span></span>
                                        </td>
                                    %else:
                                        <td class="">
                                            &nbsp;
                                        </td>
                                    %endif
                                %endif
                            %endfor
                            %if len(periodes_energia) < 6:
                                %for p in range(0, 6-len(periodes_energia)):
                                    <td class="">
                                        &nbsp;
                                    </td>
                                %endfor
                            %endif
                        %endif
                    </tr>
                    %if polissa.te_assignacio_gkwh:
                    <tr>
                        <td class="bold">${_("(1) GenerationkWh (€/kWh)")}</td>
                        %for p in periodes_energia:
                            %if polissa.llista_preu:
                                <td class="center">
                                    <span class="">${formatLang(get_gkwh_atr_price(cursor, uid, polissa, p, ctx, with_taxes=True)[0], digits=6)}</span>
                                </td>
                            %else:
                                <td class="">
                                    &nbsp;
                                </td>
                            %endif
                        %endfor
                        %if len(periodes_energia) < 6:
                            %for p in range(0, 6-len(periodes_energia)):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %endif
                    </tr>
                    %endif
                    %if polissa.autoconsumo != '00':
                    <tr>
                        <td><span class="bold auto">${_("Excedents d'autoconsum (€/kWh)")}</span></td>
                        %if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:
                            <td class="center reset_line_height" colspan="6">
                                <span class="normal_font_weight">${_(u"Tarifa indexada(2) - el preu horari de la compensació d'excedents és igual al PHM")}</span>
                            </td>
                        %else:
                            %if polissa.llista_preu:
                                <td colspan="6">
                                    <hr class="hr-text" data-content="${formatLang(get_atr_price(cursor, uid, polissa, periodes_energia[0], 'ac', ctx, with_taxes=True)[0], digits=6)}"/>
                                </td>
                            %else:
                                <td colspan="6">
                                    &nbsp;
                                </td>
                            %endif
                        %endif
                    </tr>
                    %endif
                </table>
                <div class="padding_top padding_left padding_right">
                %if polissa.te_assignacio_gkwh:
                    <span class="bold">(1) </span> ${_("Terme d'energia en cas de participar-hi, segons condicions del contracte GenerationkWh.")}<br/>
                %endif
                %if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:
                    <span class="bold">(2) </span> ${_("Pots consultar el significat de les variables a les condicions específiques que trobaràs a continuació.")}
                %endif
                </div>
            </div>
            <%
                if lead:
                    break
            %>
            %endfor
        </div>
        <div class="styled_box padding_bottom">
            <div class="center avis_impostos">
                %if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:
                    ${_(u"Els preus del terme de potència")}
                %else:
                    ${_(u"Tots els preus que apareixen en aquest contracte")}
                %endif
                &nbsp;${_(u"inclouen l'impost elèctric i l'IVA (IGIC a Canàries), amb el tipus impositiu vigent en cada moment per a cada tipus de contracte sense perjudici de les exempcions o bonificacions que puguin ser d'aplicació.")}
            </div>
        </div>
            %if text_vigencia:
                <p style="page-break-after: always"></p>
                <br><br><br>
            %endif
        % if polissa.bank:
        <div class="styled_box">
            <h5> ${_("DADES DE PAGAMENT")} </h5>
            <% iban = polissa.bank and polissa.bank.printable_iban[5:] or '' %>
            <div class="dades_pagament">
                <div class="iban"><b>${_(u"Nº de compte bancari (IBAN): **** **** **** ****")}</b> &nbsp ${iban[-4:]}</div>
            </div>
        </div>
        % endif
        <div class="modi_condicions">
            <p>
               ${_(u"Al contractar s’accepten aquestes ")}
                %if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:
                    ${_(u"Condicions Particulars, Específiques i les Condicions Generals,")}
                %else:
                    ${_(u"Condicions Particulars i les Condicions Generals")}
                %endif
               ${_(u"que es poden consultar a les pàgines següents. Si ens cal modificar-les, a la clàusula 9 de les Condicions Generals s’explica el procediment que seguirem. En cas que hi hagi alguna discrepància, prevaldrà el que estigui previst en aquestes Condicions Particulars.")}
            </p>
        </div>
        <div id="footer">
            <div class="city_date">
            <%
                data_firma =  datetime.today()
                imd_obj = obj.pool.get('ir.model.data')
                polissa_categ_obj = obj.pool.get('giscedata.polissa.category')
                polissa_categ_id = imd_obj.get_object_reference(
                    cursor, uid, 'som_polissa', 'categ_tarifa_empresa'
                )[1]
                polissa_categ = polissa_categ_obj.browse(cursor, uid, polissa_categ_id)
            %>
                ${company.partner_id.address[0]['city']},
                ${_(u"a {0}".format(localize_period(data_firma, lang)))}
            </div>
            <div class="acceptacio_digital">
                % if polissa_categ in polissa.category_id:
                    <div><b>${_(u"La contractant")}</b></div>
                % else:
                    <div><b>${_(u"La persona clienta:")}</b></div>
                % endif

                %if not lead:
                    <img src="${addons_path}/som_polissa_condicions_generals/report/assets/acceptacio_digital.png"/>
                %endif

                % if polissa_categ in polissa.category_id:
                    <div class="acceptacio_digital_txt">${_(u"Signat digitalment")}</div>
                % elif not lead:
                    <div class="acceptacio_digital_txt">${_(u"Acceptat digitalment via formulari web")}</div>
                % endif

                <div><b>${polissa.pagador.name if not pas01 else dict_titular['client_name']}</b></div>
            </div>
            <div class="signatura">
                <div><b>${_(u"La comercialitzadora")}</b></div>
                <img src="${addons_path}/som_polissa_condicions_generals/report/assets/signatura_contracte.png"/>
                <div><b>${company.name}</b></div>
            </div>
            <div class="observacions">
                ${polissa.print_observations or ""}
            </div>
        </div>
        %if polissa.state == 'esborrany':
            <div class="esborrany_footer">
                <p>
                   ${_(u"Aquestes Condicions Particulars estan condicionades a possibles modificacions amb la finalitat d'ajustar-les a les condicions tècniques d'accés a xarxa segons la clàusula 6.3 de les Condicions Generals.")}
                </p>
            </div>
        %endif

        %if obj != objects[-1]:
            <p style="page-break-after:always;"></p>
        %endif

    %endfor
    <p style="page-break-after:always;"></p>
    <%
        prova_pilot_indexada = False
        for category in polissa.category_id:
            if category.name == "Prova pilot indexada":
                prova_pilot_indexada = True
                break
    %>
    %if lang == 'ca_ES':
        <%include file="/som_polissa_condicions_generals/report/condicions_generals.mako"/>
        %if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:
            <p style="page-break-after:always;"></p>
            <%include file="/som_polissa_condicions_generals/report/condicions_especifiques_indexada.mako"/>
            %if prova_pilot_indexada:
                <p style="page-break-after:always;"></p>
                <%include file="/som_polissa_condicions_generals/report/annex_prova_pilot_indexada.mako"/>
            %endif
        %endif
    %else:
        <%include file="/som_polissa_condicions_generals/report/condiciones_generales.mako"/>
        %if (polissa.mode_facturacio == 'index' and not modcon_pendent_periodes) or modcon_pendent_indexada:
            <p style="page-break-after:always;"></p>
            <%include file="/som_polissa_condicions_generals/report/condiciones_especificas_indexada.mako"/>
            %if prova_pilot_indexada:
                <p style="page-break-after:always;"></p>
                <%include file="/som_polissa_condicions_generals/report/anexo_prueba_piloto_indexada.mako"/>
            %endif
        %endif
    %endif
</body>
</html>
