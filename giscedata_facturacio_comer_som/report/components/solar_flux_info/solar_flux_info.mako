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
        % if sf.suns_generated > 0:
            ${_(u"En aquesta factura has generat <b>%s</b> kWh d'excedents d’autoproducció, que tenen un valor de    <b>%s</b> €. A través de la compensació simplificada se t’han compensat <b>%s</b> €, i els  <b>%s</b> € restants se’t convertiran en   <b>%s</b> Sols (cada euro no compensat equival a 0,8 Sols).") % ((formatLang(sf.surplus_kwh), formatLang(sf.surplus_e), formatLang(sf.compensation_e), formatLang(sf.ajustment_e), formatLang(sf.suns_generated)))}
            <br>
            ${_(u"A partir de demà s’actualitzaran els Sols que tens disponibles a l’")}<a href=${sf.link_ov_suns}>${_(u"Oficina Virtual")}</a> ${_(u"i a les properes factures se’t transformaran en descomptes.")}
        % elif sf.compensation_e > 0:
            ${_(u"En aquesta factura has generat <b>%s</b> kWh d'excedents d’autoproducció, que tenen un valor de    <b>%s</b> €. A través de la compensació simplificada se t’han compensat <b>%s</b> €  (la totalitat dels excedents generats).") % ((formatLang(sf.surplus_kwh), formatLang(sf.surplus_e), formatLang(sf.compensation_e)))}
            <br>
            ${_(u"Per tant, en aquesta factura no es generen Sols. Pots consultar els teus Sols disponibles a la teva")} <a href=${sf.link_ov_suns}>${_(u"Oficina Virtual")}</a>.
        % else:
            ${_(u"En aquesta factura no han quedat")} <a href=${sf.link_no_compens}>${_(u"excedents sense compensar")}</a> . ${_(u"Si has autoconsumit i compensat tota la generació, ben aprofitada!.")}
            <br>
            ${_(u"Per tant, en aquesta factura no es generen Sols. Pots consultar els teus Sols disponibles a la teva")} <a href=${sf.link_ov_suns}>${_(u"Oficina Virtual")}</a>.
        % endif
        <br>
        ${_(u"Al nostre Centre d’Ajuda tens més detalls del càlcul de Sols i del sistema de")} <a href=${sf.link_help}>${_(u"Flux Solar")}</a>.
        </td>
    </tr>
    </table>
</div>
% endif
