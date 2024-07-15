<%page args="sf" />
<style>
<%include file="solar_flux_info.css" />
</style>
% if sf.is_visible:
<div class="sf_info">
    <h1>${_(u"INFORMACIÓ DEL FLUX SOLAR")}</h1>
    <table class="sf_table">
    <tr>
        <td class="text">
        % if sf.suns > 0:
            ${_(u"Amb aquesta factura has generat <b>%s</b> kWh d'excedents d’autoproducció, que tenen un valor de <b>%s</b> €. A través de la compensació simplificada se t’han compensat <b>%s</b> €, i els <b>%s</b> € restants se’t convertiran en <b>%s</b> Sols (cada euro no compensat equival a 0,8 Sols).") % ((formatLang(sf.surplus_kwh), formatLang(sf.surplus_e), formatLang(sf.compensated_e), formatLang(sf.rest_e), formatLang(sf.suns)))}
            <br>
            ${_(u"A partir de demà podràs veure aquests Sols a la teva Oficina Virtual, i a les properes factures se’t transformaran en descomptes.")}
        % elif sf.case == '2.1':
                ${_(u"En aquesta factura no s'apliquen descomptes per Flux Sols perquè no tens Sols acumulats.")}
        % elif sf.case == '2.2':
            ${_(u"Amb aquesta factura no has generat excedents d'autoproducció (ben aprofitats!).")}
            ${_(u"Per tant, en aquesta factura no es generen Sols. Pots consultar els teus Sols disponibles a la teva Oficina Virtual.")}
        % else:
            ${_(u"Cas no contemplat")}
        % endif
        <br>
        ${_(u"Tens més detalls del càlcul de Sols i del sistema de")} <a href=${sf.link_help}>Flux Solar</a> ${_(u"al nostre Centre d’Ajuda.")}
        </td>
    </tr>
    </table>
</div>
% endif
