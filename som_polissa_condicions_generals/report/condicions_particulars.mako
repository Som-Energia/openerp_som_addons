## -*- encoding: utf-8 -*-
<%
import calendar
import time, babel
from datetime import datetime
from giscedata_facturacio.report.utils import get_atr_price, get_comming_atr_price
from som_extend_facturacio_comer.utils import get_gkwh_atr_price
from giscedata_polissa.report.utils import localize_period, datetime_to_date
from gestionatr.defs import TABLA_9

def clean_text(text):
    return text or ''

CONTRACT_TYPES = dict(TABLA_9)

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
    %for polissa in objects:
        <%
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

        %if polissa.state == 'esborrany':
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
            direccio_titular = polissa.titular.address[0]
            direccio_envio = polissa.direccio_notificacio
            diferent = (polissa.direccio_notificacio != direccio_titular)
            periodes_energia, periodes_potencia = [], []
        %>
        <div class="contact_info">
            <div class="persona_titular styled_box ${"width33" if diferent else "width49"}">
                <h5>${_("PERSONA TITULAR")}</h5>
                <div class="inside_styled_box">
                    <b>${_(u"Nom/Raó social: ")}</b>
                    ${polissa.titular.name}<br/>
                    <b>${_(u"NIF/CIF: ")}</b>
                    ${polissa.titular and (polissa.titular.vat or '').replace('ES', '')}<br/>
                    <b>${_(u"Adreça: ")}</b>
                    ${clean(direccio_titular.street)}<br/>
                    <b>${_(u"Codi postal i municipi: ")}</b>
                    ${clean(direccio_titular.zip)} ${clean(direccio_titular.city)}<br/>
                    <b>${_(u"Província i país: ")}</b>
                    ${clean(direccio_titular.state_id.name)} ${clean(direccio_titular.country_id.name)}<br/>
                    <b>${_(u"Adreça electrònica: ")}</b>
                    ${clean(direccio_titular.email)}<br/>
                    <b>${_(u"Telèfon: ")}</b>
                    ${clean(direccio_titular.mobile)}<br/>
                    <b>${_(u"Telèfon 2: ")}</b>
                    ${clean(direccio_titular.phone)}<br/>
                </div>
            </div>

            <div class="dades_subministrament styled_box ${"width33" if diferent else "width49"}">
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

            %if diferent:
            <div class="dades_de_contacte styled_box ${"width33" if diferent else "width49"}">
                <h5> ${_("DADES DE CONTACTE")} </h5>
                <div class="inside_styled_box">
                    <b>${_(u"Nom/Raó social: ")}</b>
                    ${enviament(diferent, direccio_envio.name)}<br/>
                    <b>${_(u"Adreça: ")}</b>
                    ${enviament(diferent, direccio_envio.street)}<br/>
                    <b>${_(u"Codi postal i municipi: ")}</b>
                    ${enviament(diferent,
                        '{0} {1}'.format(
                            clean_text(direccio_envio.zip), clean_text(direccio_envio.city)
                        )
                    )}<br/>
                    <b>${_(u"Província i país: ")}</b>
                    ${enviament(diferent,
                        '{0} {1}'.format(
                            clean_text(direccio_envio.state_id.name), clean_text(direccio_envio.country_id.name)
                        )
                    )}<br/>
                    <b>${_(u"Adreça electrònica: ")}</b>
                    ${enviament(diferent,
                        '{0}'.format(
                            clean_text(direccio_envio.email)
                        )
                    )}<br/>
                    <b>${_(u"Telèfon: ")}</b>
                    ${enviament(diferent,
                        '{0}'.format(
                            clean_text(direccio_envio.mobile)
                        )
                    )}<br/>
                    <b>${_(u"Telèfon 2: ")}</b>
                    ${enviament(diferent,
                        '{0}'.format(
                            clean_text(direccio_envio.phone)
                        )
                    )}<br/>
                </div>
            </div>
            %endif
        </div>

        <div class="peatge_acces styled_box">
            <h5> ${_("PEATGE I CÀRRECS (definits a la Circular de la CNMC 3/2020 i al Reial decret 148/2021)")} </h5>

            <div class="peatge_access_content">
                <div class="padding_left"><b>${_(u"Peatge de transport i distribució: ")}</b>${clean(polissa.tarifa_codi)}</div>
                <%
                    autoconsum = polissa.autoconsumo
                    if autoconsum and autoconsum in TABLA_113_dict:
                        autoconsum = TABLA_113_dict[autoconsum]
                %>

                <div class="padding_bottom padding_left"><b>${_(u"Tipus de contracte: ")}</b> ${CONTRACT_TYPES[polissa.contract_type]} ${"({0})".format(autoconsum) if polissa.autoconsumo != '00' else ""}</div>

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
                            potencies = polissa.potencies_periode
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
                                <span>${formatLang(periodes[0][1].potencia, digits=3)}</span>
                            %endif
                            </td>
                            <td></td>
                            <td class="center">
                            %if periodes[2][1] and periodes[2][1].potencia:
                                <span>${formatLang(periodes[2][1].potencia, digits=3)}</span>
                            %endif
                            </td>
                        %else:
                            %for p in periodes:
                                <td class="center">
                                %if p[1] and p[1].potencia:
                                    <span>${formatLang(p[1].potencia, digits=3)}</span>
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
            else:
                tarifes_a_mostrar = get_comming_atr_price(cursor, uid, polissa, ctx)
            text_vigencia = ''

            if not polissa.fiscal_position_id:
                imd_obj = polissa.pool.get('ir.model.data')
                if polissa.potencia <= 10:
                    fp_id = imd_obj.get_object_reference(cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
                else:
                    fp_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio', 'fp_nacional_2021_rd_17_2021')[1]
                ctx.update({'force_fiscal_position': fp_id})

            cfg_obj = polissa.pool.get('res.config')
            start_date_mecanisme_ajust_gas = cfg_obj.get(
            cursor, uid, 'start_date_mecanisme_ajust_gas', '2022-10-01'
            )
            end_date_mecanisme_ajust_gas = cfg_obj.get(
                cursor, uid, 'end_date_mecanisme_ajust_gas', '2099-12-31'
            )
        %>
        <div class="styled_box">
        %for dades_tarifa in tarifes_a_mostrar:
            <%
                if not data_final and dades_tarifa['date_end']:
                    text_vigencia = _(u"(vigents fins al {})").format(dades_tarifa['date_end'])
                elif dades_tarifa['date_end'] and dades_tarifa['date_start']:
                    text_vigencia = _(u"(vigents fins al {})").format((datetime.strptime(dades_tarifa['date_end'], '%Y-%m-%d')).strftime('%d/%m/%Y'))
                elif datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d') > datetime.today():
                    text_vigencia = _(u"(vigents a partir del {})").format(datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d').strftime('%d/%m/%Y'))
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
                    if periodes:
                        if data_final: #TODO: A LA SEGONA PASSADA, POSARIEM ELS PREUS VELLS
                            data_llista_preus = dades_tarifa['date_start']
                            if datetime.strptime(data_llista_preus, '%Y-%m-%d') <= datetime.today():
                                data_llista_preus = min(datetime.strptime(data_final, '%Y-%m-%d'), datetime.today())
                            ctx['date'] = data_llista_preus
                        data_i = data_inici and datetime.strptime(polissa.modcontractual_activa.data_inici, '%Y-%m-%d')
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
                                    <td class="">
                                        &nbsp;
                                    </td>
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
                        %if polissa.mode_facturacio == 'index':
                            <td class="center reset_line_height" colspan="6">
                                <span class="normal_font_weight">
                                    %if lang ==  'ca_ES':
                                        <a target="_blank" href="https://www.somenergia.coop/documentacio_EiE/CA_EiE_Explica_Tarifa%20Indexada%20per%20Entitats%20i%20Empreses_Som%20Energia.pdf">
                                            <b>${_(u"Tarifa indexada")}</b>
                                        </a>
                                    %else:
                                        <a target="_blank" href="https://www.somenergia.coop/documentacio_EiE/ES_EiE_Explica_Tarifa%20Indexada%20para%20Entidades%20y%20Empresas_Som%20Energia.pdf">
                                            <b>${_(u"Tarifa indexada")}</b>
                                        </a>
                                    %endif
                                    ${_(u" - el preu horari es calcula d'acord amb la fórmula:")}
                                </span>
                                <br/>
                                <span>${_(u"PH = 1,015 * [(PHM + PHMA + Pc + SobrecostosREE + Interrump + POsOm) (1 + Perd) + FE + K] + PA + CA")}</span>
                                <br/>
                                <span class="normal_font_weight">${_(u"on el marge de comercialització")}</span>
                                <span>&nbsp;${("(K) = %s €/MWh</B>") % formatLang((polissa.coeficient_k + polissa.coeficient_d), digits=3)}</span>
                            </td>
                        %else:
                            %for p in periodes_energia:
                                %if polissa.llista_preu:
                                    <td class="center">
                                        <span class="">${formatLang(get_atr_price(cursor, uid, polissa, p, 'te', ctx, with_taxes=True)[0], digits=6)}</span>
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
                        <td><span class="bold">${_("(2) Autoconsum (€/kWh)")}</span></td>
                        %if polissa.mode_facturacio == 'index':
                            <td class="center reset_line_height" colspan="6">
                                <span class="normal_font_weight">${_(u"Tarifa indexada - el preu es calcula d'acord amb la fórmula:")}</span>
                                <br/>
                                <span>${_(u"Import excedents = Suma horària (kWh excedentaris h <sub>i</sub> * PHM <sub>i</sub> )")}</span>
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
                %if polissa.autoconsumo != '00':
                    <span class="bold">(2) </span> ${_("Preu de la compensació d'excedents, si és aplicable.")}
                %endif
                </div>
                %if polissa.mode_facturacio != 'index' and dades_tarifa['date_start'] >= start_date_mecanisme_ajust_gas and \
                    (not dades_tarifa['date_end'] or dades_tarifa['date_end'] <= end_date_mecanisme_ajust_gas):
                    <div class="avis_rmag">
                        ${_(u"A més del preu fix associat al cost de l'energia, establert per Som Energia i publicat a la nostra pàgina web, la factura inclourà un import variable associat al mecanisme d'ajust establert al")}
                        &nbsp;<a target="_blank" href="https://www.boe.es/buscar/act.php?id=BOE-A-2022-10557">RD 10/2022</a>.
                        ${_(u"Aquest import el calcularem per a cada període de facturació. Ponderarem el preu de cada hora del mecanisme d'ajust (")}<a target="_blank" href="https://www.omie.es/es/market-results/daily/average-final-prices/hourly-price-consumers">${_(u"publicat per OMIE")}</a>
                        ${_(u") en funció del repartiment horari energètic d'un consumidor/a tipus (")}<a target="_blank" href="https://www.ree.es/es/clientes/consumidor/gestion-medidas-electricas/consulta-perfiles-de-consumo">${_(u"publicat per Red Eléctrica de")}</a>
                        <a target="_blank" href="https://www.ree.es/es/clientes/consumidor/gestion-medidas-electricas/consulta-perfiles-de-consumo">&nbsp;España</a>
                        &nbsp;${_(u"segons la")}&nbsp;<a target="_blank" href="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2021-21395">${_(u"Resolució de 23/12/2021")}</a>
                        ${_(u"). El preu obtingut el multiplicarem, en cada factura, per l'energia total consumida en el període de facturació. El mecanisme d’ajust al gas no aplica per als contractes de les Illes Canàries ni Balears, i tampoc aplica a la tarifa Generation kWh.")}
                    </div>
                %endif
            </div>
            %endfor
        </div>
        <div class="styled_box padding_bottom">
            <div class="center avis_impostos">
                %if polissa.mode_facturacio == 'index':
                    ${_(u"Els preus del terme de potència")}
                %else:
                    ${_(u"Tots els preus que apareixen en aquest contracte")}
                %endif
                &nbsp;${_(u"inclouen l'impost elèctric i l'IVA (IGIC a Canàries), amb el tipus impositiu vigent en cada moment per a cada tipus de contracte. Actualment, d'acord amb el")}&nbsp;<a target="_blank" href="https://www.boe.es/buscar/act.php?id=BOE-A-2022-10557">${_(u"Reial Decret-llei 11/2022")}</a>, ${_(u"l’IVA aplicable serà del")}&nbsp;
                %if polissa.potencia <= 10:
                    ${_(u"5% (sempre que el preu mitjà del mercat majorista del mes anterior al de facturació hagi estat superior a 45€/MWh. En cas que hagi estat inferior, l’IVA que s’aplicarà serà del 21%).")}
                %else:
                    ${_(u"21%.")}
                %endif
                &nbsp;${_(u"També, i seguint el Reial Decret-Llei 11/2022, els preus inclouen l’Impost Especial sobre l’Electricitat rebaixat al 0,5% (amb una quota mínima de 0,5 €/MWh o 1 €/MWh, segons correspongui).")}
            </div>
        </div>
            <%
                owner_b = polissa.bank.partner_id.name
                nif = polissa.bank.partner_id.vat
                pol_bank = polissa.bank.read(['owner_id'])
                if 'owner_id' in pol_bank and polissa.bank.owner_name:
                    owner_b = polissa.bank.owner_name
                    if polissa.bank.owner_id:
                        nif = polissa.bank.owner_id.vat
                nif = nif.replace('ES', '')
            %>
            %if text_vigencia:
                <p style="page-break-after: always"></p>
                <br><br><br>
            %endif
        <div class="styled_box">
            <h5> ${_("DADES DE PAGAMENT")} </h5>
            <% iban = polissa.bank and polissa.bank.printable_iban[5:] or '' %>
            <div class="dades_pagament">
                <div class="titular">
                    <span class="name"><b>${_(u"Persona titular del compte: ")}</b> ${owner_b}</span>
                    <span class="nif"><b>${_(u"NIF: ")}</b> ${nif}</span>
                </div>
                </br>
                <div class="iban"><b>${_(u"Nº de compte bancari (IBAN): **** **** **** ****")}</b> &nbsp ${iban[-4:]}</div>
            </div>
        </div>
        <div class="modi_condicions">
            <p>
               ${_(u"Al contractar s’accepten aquestes Condicions Particulars i les Condicions Generals, que es poden consultar a les pàgines següents. Si ens cal modificar-les, a la clàusula 9 de les Condicions Generals s’explica el procediment que seguirem. En cas que hi hagi alguna discrepància, prevaldrà el que estigui previst en aquestes Condicions Particulars.")}
            </p>
        </div>
        <div id="footer">
            <div class="city_date">
            <%
                if polissa.data_firma_contracte:
                    data_firma =  datetime.strptime(datetime_to_date(polissa.data_firma_contracte), '%Y-%m-%d')
                else:
                    data_firma =  datetime.today()
            %>
                ${company.partner_id.address[0]['city']},
                ${_(u"a {0}".format(localize_period(data_firma, lang)))}
            </div>
            <div class="acceptacio_digital">
                <div><b>${_(u"La persona clienta:")}</b></div>
                <img src="${addons_path}/som_polissa_condicions_generals/report/assets/acceptacio_digital.png"/>
                <div class="acceptacio_digital_txt">${_(u"Acceptat digitalment via formulari web")}</div>

                <div><b>${polissa.pagador.name}</b></div>
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

        %if polissa != objects[-1]:
            <p style="page-break-after:always;"></p>
        %endif

    %endfor
    <p style="page-break-after:always;"></p>
    %if lang == 'ca_ES':
        <%include file="/som_polissa_condicions_generals/report/condicions_generals.mako"/>
    %else:
        <%include file="/som_polissa_condicions_generals/report/condiciones_generales.mako"/>
    %endif
</body>
</html>
