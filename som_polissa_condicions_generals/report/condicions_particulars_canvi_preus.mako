## -*- encoding: utf-8 -*-
<%
import collections
from datetime import datetime
from giscedata_polissa.report.utils import localize_period, datetime_to_date
from gestionatr.defs import TABLA_9

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

def clean_text(text):
    return text or ''



TARIFF_PRICES = {
    "2.0TD": {
        "power": [
            ("P1", 36.211537),
            ("P2", 3.743002),
        ],
        "energy": [
            ("P1", 0.494932),
            ("P2", 0.389136),
            ("P3", 0.318605),
        ],
        "gkwh": [
            ("P1", 0.254154),
            ("P2", 0.166599),
            ("P3", 0.133766),
        ]
    },
    "3.0TD": {
        "power": [
            ("P1", 20.271820),
            ("P2", 14.888511),
            ("P3", 7.216142),
            ("P4", 6.138997),
            ("P5", 4.096148),
            ("P6", 2.617202),
        ],
        "energy": [
            ("P1", 0.470611),
            ("P2", 0.425618),
            ("P3", 0.387920),
            ("P4", 0.356303),
            ("P5", 0.323469),
            ("P6", 0.307661),
        ],
        "gkwh": [
            ("P1", 0.198216),
            ("P2", 0.177543),
            ("P3", 0.145926),
            ("P4", 0.130117),
            ("P5", 0.114309),
            ("P6", 0.121605),
        ]
    },
    "6.1TD": {
        "power": [
            ("P1", 30.075436),
            ("P2", 26.180760),
            ("P3", 14.981664),
            ("P4", 12.035562),
            ("P5", 3.446188),
            ("P6", 1.910529),
        ],
        "energy": [
            ("P1", 0.413457),
            ("P2", 0.376976),
            ("P3", 0.353871),
            ("P4", 0.324685),
            ("P5", 0.295500),
            ("P6", 0.280908),
        ],
        "gkwh": [
            ("P1", 0.139846),
            ("P2", 0.126469),
            ("P3", 0.108228),
            ("P4", 0.098500),
            ("P5", 0.085124),
            ("P6", 0.093636),
        ]
    },
    "3.0TDVE": {
        "power": [
            ("P1", 3.162660),
            ("P2", 2.755890),
            ("P3", 1.113789),
            ("P4", 0.847293),
            ("P5", 0.333368),
            ("P6", 0.333368),
        ],
        "energy": [
            ("P1", 0.594648),
            ("P2", 0.522902),
            ("P3", 0.441426),
            ("P4", 0.387920),
            ("P5", 0.331982),
            ("P6", 0.313741),
        ],
        "gkwh": [
            ("P1", 0.322253),
            ("P2", 0.274827),
            ("P3", 0.198216),
            ("P4", 0.161735),
            ("P5", 0.122821),
            ("P6", 0.127685),
        ]
    },
    "6.1TDVE": {
        "power": [
            ("P1", 4.995486),
            ("P2", 4.995486),
            ("P3", 2.723603),
            ("P4", 2.062970),
            ("P5", 0.136993),
            ("P6", 0.136993),
        ],
        "energy": [
            ("P1", 0.606809),
            ("P2", 0.531414),
            ("P3", 0.440210),
            ("P4", 0.378192),
            ("P5", 0.305229),
            ("P6", 0.288204),
        ],
        "gkwh": [
            ("P1", 0.333198),
            ("P2", 0.280908),
            ("P3", 0.194568),
            ("P4", 0.152006),
            ("P5", 0.094852),
            ("P6", 0.099716),
        ]
    },
}
def calcularPreuCanaries(periodes, fiscal_position):
    if fiscal_position.id in [19,33]:
        igic = 1.03
    elif fiscal_position.id in [25,34]:
        igic = 1.0
    else:
        return periodes

    for k,v in periodes.items():
        periodes[k] = round(((v / 1.21)) * igic, 6)

    return periodes

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
                    <b>${_(u"Contracte núm.")}</b> ${polissa.name}<br/>
                    <b>${_(u"Data d'inici del subministrament:")}</b>
                    %if polissa.state == 'esborrany':
                        &nbsp;
                    %else:
                        ${formatLang(data_inici, date=True)}
                    %endif
                    <br/>
                    <b>${_(u"Data de renovació del subministrament:")}</b>
                    %if polissa.state == 'esborrany':
                        &nbsp;
                    %else:
                        ${formatLang(data_final, date=True)}
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
                    <b>${_(u"Nom/Raó social:")}</b>
                    ${polissa.titular.name}<br/>
                    <b>${_(u"NIF/CIF:")}</b>
                    ${polissa.titular and (polissa.titular.vat or '').replace('ES', '')}<br/>
                    <b>${_(u"Adreça:")}</b>
                    ${clean(direccio_titular.street)}<br/>
                    <b>${_(u"Codi postal i municipi:")}</b>
                    ${clean(direccio_titular.zip)} ${clean(direccio_titular.city)}<br/>
                    <b>${_(u"Província i país:")}</b>
                    ${clean(direccio_titular.state_id.name)} ${clean(direccio_titular.country_id.name)}<br/>
                    <b>${_(u"Adreça electrònica:")}</b>
                    ${clean(direccio_titular.email)}<br/>
                    <b>${_(u"Telèfon:")}</b>
                    ${clean(direccio_titular.mobile)}<br/>
                    <b>${_(u"Telèfon 2:")}</b>
                    ${clean(direccio_titular.phone)}<br/>
                </div>
            </div>

            <div class="dades_subministrament styled_box ${"width33" if diferent else "width49"}">
                <h5> ${_("DADES DEL PUNT DE SUBMINISTRAMENT")} </h5>

                <div class="inside_styled_box">
                    <b>${_(u"Adreça:")}</b>
                    ${polissa.cups.direccio}</br>
                    <b>${_(u"Província i país:")}</b>
                    ${polissa.cups.id_provincia.name} ${polissa.cups.id_provincia.country_id.name}</br>
                    <b>${_(u"CUPS:")}</b>
                    ${polissa.cups.name}</br>
                    <b>${_(u"CNAE:")}</b>
                    ${polissa.cnae.name}</br>
                    <b>${_(u"Contracte d'accés:")}</b>
                    ${clean(polissa.ref_dist)}</br>
                    <b>${_(u"Activitat principal:")}</b>
                    ${polissa.cnae.descripcio}</br>
                    <b>${_(u"Empresa distribuïdora:")}</b>
                    ${polissa.cups.distribuidora_id.name}</br>
                    <b>${_(u"Tensió Nominal (V):")}</b>
                    ${clean(polissa.tensio)}</br>
                </div>
            </div>

            %if diferent:
            <div class="dades_de_contacte styled_box ${"width33" if diferent else "width49"}">
                <h5> ${_("DADES DE CONTACTE")} </h5>
                <div class="inside_styled_box">
                    <b>${_(u"Nom/Raó social:")}</b>
                    ${enviament(diferent, direccio_envio.name)}<br/>
                    <b>${_(u"Adreça:")}</b>
                    ${enviament(diferent, direccio_envio.street)}<br/>
                    <b>${_(u"Codi postal i municipi:")}</b>
                    ${enviament(diferent,
                        '{0} {1}'.format(
                            clean_text(direccio_envio.zip), clean_text(direccio_envio.city)
                        )
                    )}<br/>
                    <b>${_(u"Província i país:")}</b>
                    ${enviament(diferent,
                        '{0} {1}'.format(
                            clean_text(direccio_envio.state_id.name), clean_text(direccio_envio.country_id.name)
                        )
                    )}<br/>
                    <b>${_(u"Adreça electrònica:")}</b>
                    ${enviament(diferent,
                        '{0}'.format(
                            clean_text(direccio_envio.email)
                        )
                    )}<br/>
                    <b>${_(u"Telèfon:")}</b>
                    ${enviament(diferent,
                        '{0}'.format(
                            clean_text(direccio_envio.mobile)
                        )
                    )}<br/>
                    <b>${_(u"Telèfon 2:")}</b>
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
                <div class="padding_bottom padding_left"><b>${_(u"Tarifa contractada: ")}</b>${clean_text(polissa.tarifa_codi)}</div>

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

                            if len(potencies) < 3:
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
                                    <span>${p[1] and p[1].potencia or ' '}</span>
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
                <%
                    autoconsum = polissa.autoconsumo
                    if autoconsum and autoconsum in TABLA_113_dict:
                        autoconsum = TABLA_113_dict[autoconsum]
                %>

                <div class="padding_top padding_left"><b>${_(u"Tipus de contracte: ")}</b> ${CONTRACT_TYPES[polissa.contract_type]} ${"({0})".format(autoconsum) if polissa.autoconsumo != '00' else ""}</div>
            </div>
        </div>

        <div class="styled_box">
            <h5> ${_("TARIFES D'ELECTRICITAT")}</h5>

            <div class="tarifes_electricitat">
                <%
                    periodes_potencia = calcularPreuCanaries(collections.OrderedDict(TARIFF_PRICES[polissa.tarifa_codi]['power']), polissa.fiscal_position_id)
                    periodes_energia = calcularPreuCanaries(collections.OrderedDict(TARIFF_PRICES[polissa.tarifa_codi]['energy']), polissa.fiscal_position_id)
                    periodes_gkwh = calcularPreuCanaries(collections.OrderedDict(TARIFF_PRICES[polissa.tarifa_codi]['gkwh']), polissa.fiscal_position_id)
                %>
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
                                    <span>${periodes_potencia.values()[0]}</span>
                                </td>
                                <td></td>
                                <td class="center">
                                    <span>${periodes_potencia.values()[1]}</span>
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
                            %for p in periodes_potencia.values():
                                %if polissa.llista_preu:
                                    <td class="center">
                                        <span><span>${formatLang(p, digits=6)}</span></span>
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
                        %for p in periodes_energia.values():
                            <td class="center">
                                <span class="">${p}</span>
                            </td>
                        %endfor
                        %if len(periodes_energia) < 6:
                            %for p in range(0, 6-len(periodes_energia)):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %endif
                    </tr>
                    <tr>
                        <td class="bold">${_("(1) GenerationkWh (€/kWh)")}</td>
                        %for p in periodes_gkwh.values():
                            <td class="center">
                                <span class="">${p}</span>
                            </td>
                        %endfor
                        %if len(periodes_gkwh) < 6:
                            %for p in range(0, 6-len(periodes_gkwh)):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %endif
                    </tr>
                    <tr>
                        <td class="bold">${_("(2) Autoconsum (€/kWh)")}</td>
                        <td colspan="6">
                            <hr class="hr-text" data-content="0.240778"/>
                        </td>
                    </tr>
                </table>
                <div class="padding_top padding_left padding_right">
                    <span class="bold">(1) ${_("Terme d'energia en cas de participar-hi, segons condicions del contracte GenerationkWh.")}</span><br/>
                    <span class="bold">(2) ${_("Preu de la compensació d'excedents, si és aplicable.")}</span>
                    <div class="center avis_impostos">
                       ${_(u"Aquests preus inclouen l'impost elèctric i l'IVA sense prejudici de les exempcions o bonificacions que puguin ser d'aplicació. Pots consultar altres conceptes que poden ser d'aplicació, com ara, el lloguer de comptador, el recàrrec per potència demandada o el recàrrec per energia reactiva, a la ")}
                        %if lang ==  'ca_ES':
                            <a href="https://www.somenergia.coop/tarifes-d-electricitat/">${_(u"pàgina de tarifes")}</a>
                        %else:
                            <a href="https://www.somenergia.coop/tarifas-de-electricidad/">${_(u"página de tarifas")}</a>
                        %endif
                        ${_(u" del nostre web, on també trobaràs més informació sobre els períodes tarifaris.")}
                    </div>
                </div>
            </div>
            <%
                owner_b = ''
                if polissa.pagador.name:
                    owner_b = polissa.pagador.name
                nif = polissa.pagador.vat or ''
                nif = nif.replace('ES', '')
            %>
        </div>
        <div class="modi_condicions">
            <p>
               ${_(u"Al contractar s’accepten aquestes Condicions Particulars i les Condicions Generals, que es poden consultar a les pàgines següents. Si ens cal modificar-les, a la clàusula 9 de les Condicions Generals s’explica el procediment que seguirem. En cas que hi hagi alguna discrepància, prevaldrà el que estigui previst en aquestes Condicions Particulars.")}
            </p>
        </div>
        <div class="styled_box">
            <h5> ${_("DADES DE PAGAMENT")} </h5>
            <% iban = polissa.bank and polissa.bank.printable_iban[5:] or '' %>
            <div class="dades_pagament">
                <div class="titular">
                    <span class="name"><b>${_(u"Persona titular del compte:")}</b> ${owner_b}</span>
                    <span class="nif"><b>${_(u"NIF:")}</b> ${nif}</span>
                </div>
                </br>
                <div class="iban"><b>${_(u"Nº de compte bancari (IBAN):")}</b> ${iban}</div>
            </div>
        </div>
        <div id="footer">
            <div class="city_date">
            <%
                entrada_en_vigor = str(datetime(year=2022, month=2, day=1))
                data_firma =  datetime.strptime(datetime_to_date(entrada_en_vigor), '%d/%m/%Y')
            %>
                ${company.partner_id.address[0]['city']},
                ${_(u"a {0}".format(localize_period(data_firma, lang)))}
            </div>
            <div class="acceptacio_digital">
                <div><b>${_(u"La persona clienta:")}</b></div>
                <img src="${addons_path}/som_polissa_condicions_generals/report/assets/acceptacio_digital.png"/>
                <div class="acceptacio_digital_txt">Acceptat digitalment via formulari web</div>

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

