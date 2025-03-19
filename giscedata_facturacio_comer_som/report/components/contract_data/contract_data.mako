<%page args="cd" />
<style>
<%include file="contract_data.css" />
</style>
<%
import locale
TABLA_113_dict = { # Table extracted from gestionatr.defs TABLA_113, not imported due translations issues
    '00': _(u"Sense Autoconsum"), # Sin Autoconsumo
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
    '57': _(u"Amb excedents sense compensació Col·lectiu sense cte de Serv. Aux. (menyspreable) en Xarxa Interior – Consum')"), # Con excedentes sin compensación Colectivo sin cto de SSAA (despreciable) en red interior – Consumo')
    '58': _(u"Amb excedents sense compensació Col·lectiu sense cto de Serv. Aux. a través de xarxa - Consum')"), # Con excedentes sin compensación Colectivo sin cto de SSAA a través de red - Consumo
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
            <div class="contract_data_main">
                <p>${_(u"Adreça de subministrament:")} <span style="font-weight: bold;">${cd.cups_direction}</span> <br />
                ${_(u"Potència contractada (kW):")} <span style="font-weight: bold;">${"%s (%s)" % (locale.str(locale.atof(formatLang(cd.power, digits=3))), cd.power_invoicing_type and _(u"facturació per maxímetre") or _(u"facturació per ICP") )}</span> <br />
                ${_(u"Tarifa contractada:")} <span style="font-weight: bold;">${cd.tariff}</span> <br />
                ${_(u"CUPS:")} <span style="font-weight: bold;">${cd.cups}</span> <br />
                ${_(u"Comptador telegestionat:")} <span style="font-weight: bold;">${cd.remote_managed_meter and _(u'Sí') or _(u'No')}</span> <br />
                ${_(u"CNAE:")} <span style="font-weight: bold;">${cd.cnae}</span> <br />
                ${_(u'Data d\'alta del contracte: <span style="font-weight: bold;">%s</span>, sense condicions de permanència') % cd.start_date} <br />
                ${_(u'Forma de pagament: rebut domiciliat')} <br />
                ${_(u'Data de renovació automàtica: <span style="font-weight: bold;">%s</span>') % cd.renovation_date}
                </p>
            </div>
            %if cd.is_autoconsum:
            <div class="contract_data_auto">
                <p>${_(u"Autoproducció tipus:")} <span style="font-weight: bold;">${autoconsum_text}</span> <br />
                ${_(u"Codi d'autoconsum unificat (CAU):")} <span style="font-weight: bold;">${cd.autoconsum_cau}</span>
                %if cd.is_autoconsum_colectiu:
                    <br />${_(u"Percentatge de repartiment de l'autoproducció compartida:")} <span style="font-weight: bold;">${cd.autoconsum_colectiu_repartiment} %</span>
                %endif
                </p>
            </div>
            %endif
        </div>
    </div>
