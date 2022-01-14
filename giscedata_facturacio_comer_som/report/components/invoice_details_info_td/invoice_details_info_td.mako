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
    ${_(u"L'any 2020, Som Energia ha contribuït amb 397.408,41 euros al finançament del bo social. Totes les comercialitzadores estan obligades a finançar el bo social, que només poden oferir les comercialitzadores de refèrencia.")}
    % if id_info.has_autoconsum:
        <br>
        ${_(u"(1) Segons estableix el Reial Decret 244/2019 aquest import no serà mai superior al l'import per energia utilitzada. En cas que la compensació sigui superior a l'energia utilitzada, el terme d'energia serà igual a 0€")}
    % endif
</td>
</tr>
</table>