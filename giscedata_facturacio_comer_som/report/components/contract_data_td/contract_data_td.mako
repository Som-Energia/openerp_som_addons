<%page args="cd" />
<style>
<%include file="contract_data_td.css" />
</style>
<%
import locale
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
TABLA_133_dict = { # Table extracted from gestionatr.defs TABLA_133, not imported due translations issues
    '10': _(u"Sense excedents No acollit a compensació"), # Sin excedentes No acogido a compensación
    '11': _(u"Sense excedents acollit a compensació"), # Sin excedentes acogido a compensación
    '20': _(u"Amb excedents no acollits a compensació"), # Con excedentes no acogidos a compensación
    '21': _(u"Amb excedents acollits a compensació"), # Con excedentes acogidos a compensación
    '00': _(u"Sense autoconsum"), # Sin autoconsumo
    '0C': _(u"Baixa com a membre d'autoconsum col·lectiu"), # Baja como miembro de autoconsumo colectivo
}
autoconsum_text = TABLA_133_dict[cd.autoconsum] if cd.autoconsum in TABLA_133_dict else _("")
%>
    <div class="contract_data${cd.small_text and '_small' or ''}">
        <h1>${_(u"DADES DEL CONTRACTE")}</h1>
        <div class="contract_data_container">
            <div class="contract_data_adreca">
                ${_(u"Adreça de subministrament:")} <span style="font-weight: bold;">${cd.cups_direction}</span>
            </div>
            <div class="contract_data_column">
                <p>

                    % if len(cd.powers) == 2:
                        ${_(u"Potència contractada (kW):")} ${_("Punta: <b><i>%s</i></b> - Vall: <b><i>%s</i></b>") % (locale.str(locale.atof(formatLang(cd.powers[0][1], digits=3))), locale.str(locale.atof(formatLang(cd.powers[1][1], digits=3))))}  <br />
                    % else:
                        ${_(u"Potència contractada (kW):")} ${"%s" % (" - ".join([ "{} <b><i>{}</i></b>".format(power[0],locale.str(locale.atof(formatLang(power[1], digits=3)))) for power in cd.powers]) )} <br />
                    % endif
                    % if cd.power_invoicing_type == 1:
                        ${_(u"Facturació potència:")} <span style="font-weight: bold;">${_(u"Facturació per maxímetre")}</span> <br />
                    % elif cd.power_invoicing_type == 2:
                        ${_(u"Facturació potència:")} <span style="font-weight: bold;">${_(u"Facturació per potència quarthorari")}</span> <br />
                    % else:
                        ${_(u"Facturació potència:")} <span style="font-weight: bold;">${_(u"Facturació per ICP")}</span> <br />
                    % endif
                    ${_(u"Peatge de transport i distribució:")} <span style="font-weight: bold;">${cd.tariff}</span> <br />
                    ${_(u"Segment tarifari:")} <span style="font-weight: bold;">${cd.segment_tariff}</span> <br />
                    % if cd.invoicing_mode == 'index':
                        ${_(u"Tarifa:")} <span style="font-weight: bold;">${cd.pricelist}</span> <br />
                    % endif
                    ${_(u"CUPS:")} <span style="font-weight: bold;">${cd.cups}</span> <br />
                    ${_(u"Comptador telegestionat:")} <span style="font-weight: bold;">${cd.remote_managed_meter and _(u'Sí') or _(u'No')}</span> <br />
                </p>
            </div>
            <div class="contract_data_column">
                <p>
                    ${_(u"CNAE:")} <span style="font-weight: bold;">${cd.cnae}</span> <br />
                    ${_(u'Data d\'alta del contracte: <span style="font-weight: bold;">%s</span>') % (cd.start_date)} <br />
                    ${_(u'Forma de pagament: <span style="font-weight: bold;">Rebut domiciliat</span>')} <br />
                    ${_(u'Data final del contracte: <span style="font-weight: bold;">%s</span> %s') % (cd.renovation_date, _(u'sense condicions de permanència') if not cd.has_permanence else _(u"pròrroga automàtica per períodes d'un any"))} <br/>
                    %if cd.is_autoconsum:
                        ${_(u"Autoproducció tipus:")} <span style="font-weight: bold;">${autoconsum_text}</span> <br />
                        % for autoconsum_cau in cd.autoconsum_caus:
                            ${_(u"CAU (Codi d'autoconsum unificat):")} <span style="font-weight: bold;">${autoconsum_cau}</span> <br />
                        % endfor
                    %endif
                </p>
            </div>
        </div>
    </div>
