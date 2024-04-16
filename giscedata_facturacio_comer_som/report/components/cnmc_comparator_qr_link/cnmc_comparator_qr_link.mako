<%page args="comparator" />
<style>
<%include file="cnmc_comparator_qr_link.css" />
</style>
<%
    generation_link = "https://www.somenergia.coop/ca/tarifes-d-electricitat/" if comparator.lang == 'ca_es' else "https://www.somenergia.coop/es/tarifas-de-electricidad/"
%>
% if comparator.is_visible:
<div class="qr_info">
    <h1>${_(u"COMPARADOR DE PREUS DE LA CNMC")}</h1>
    <table class="qr_table">
    <tr>
        <td class="text">
            ${_(u"Amb aquest codi QR o bé amb l’enllaç ")}<a href=${comparator.link_qr}>comparador.cnmc.gob.es</a>&nbsp${_(u"pots consultar i comparar les diferents ofertes vigents de les comercialitzadores d’electricitat del mercat lliure.")}
        % if comparator.has_gkwh:
            ${_(u"Recorda que tens ")}<a href=${generation_link}>${_(u"tarifa Generation kWh")}</a> ${_(u", que té un preu diferent de la tarifa general, i que el comparador no la té en compte.")}
        % endif
    % if comparator.qr_image:
        </td>
        <td class="qr"> <img class="qr_img" src="${'data:image/png;base64, {}'.format(comparator.qr_image)}"> </td>
    % else:
        ${_(u"(no disposem de les dades suficients per omplir els camps del formulari)")}
        </td>
        <td class="qr"> <img class="qr_img" src="${addons_path}/giscedata_facturacio_comer_som/report/components/cnmc_comparator_qr_link/generic_qr_comparator.png"> </td>
    % endif
    </tr>
    </table>
</div>
% endif
