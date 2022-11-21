<%page args="id_info" />
<style>
<%include file="invoice_details_info_td.css" />
</style>

<table class="invoice_details_info_td_indivisible">
<tr>
<td class="td_circle"> <span class="circle">i<span></td>
<td class="td_text">
    ${_(u"Els preus dels termes de peatges de transport i distribució són els publicats en el BOE núm. 70, de 23 de març de 2021. Els preus dels càrrecs són els publicats a l'Ordre TED/371/2021. Els preus del lloguer dels comptadors són els publicats a l'Ordre ITC/3860/2007.")}
    <br>
    % if id_info.has_mag:
        ${_(u"Les comercialitzadores del mercat lliure poden triar voluntàriament repercutir l'import de l'energia associada a la compensació del mecanisme ibèric regulat pel Reial Decret-llei 10/2022, del 13 de maig, dins dels costos d'aprovisionament, o bé traslladar-lo de manera diferenciada als seus consumidors. En aquest cas, la seva comercialitzadora ha optat per aquesta última opció.")}
        <br>
        ${_(u"Preu mitjà del Mecanisme d'Ajust el darrer mes natural complet ha estat de %s €/kWh, segons estableix el RD-L 18/2022.") % (formatLang(id_info.preu_mitja_mag_darrer_mes))}
        <br>
        ${_(u"L'efecte reductor del Mecanisme d'Ajust regulat al RD-L 18/2022 sobre el preu del mercat majorista de l'energia en el període comprès en aquesta factura ha estat de %s €/MWh, considerant que el preu mitjà del mercat majorista sense ajustament hagués estat de %s €/MWh (preu mitjà OMIE + mitjana de la quantia unitària) mentre que el preu mitjà amb ajustament ha estat de %s €/MWh (preu mitjà OMIE + mitjana del cost del MAG)") % (formatLang(id_info.reductor_mag), formatLang(id_info.majorista_amb_mag), formatLang(id_info.majorista_sense_mag) )}
    % endif
    % if id_info.has_autoconsum:
        <br>
        ${_(u"(1) Segons estableix el Reial Decret 244/2019 aquest import no serà mai superior al l'import per energia utilitzada. En cas que la compensació sigui superior a l'energia utilitzada, el terme d'energia serà igual a 0€")}
    % endif
</td>
</tr>
</table>