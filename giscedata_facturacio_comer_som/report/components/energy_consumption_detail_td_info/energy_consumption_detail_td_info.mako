<%page args="id_info,col" />
<style>
<%include file="energy_consumption_detail_td_info.css" />
</style>

<table>
<tr>
<td class="td_circle"> <span class="circle">i<span></td>
<td class="td_text">
    ${_(u"(1) La despesa diària és de %s €, que correspon a %s kWh/dia (%s dies).") % (formatLang(id_info.diari_factura_actual_eur), formatLang(id_info.diari_factura_actual_kwh), id_info.dies_factura or 1)}
    <br>
    %if id_info.adjust_reason == '99':
        ${_(u"(2) Aquesta energia utilitzada inclou ajustos aplicats per la companyia distribuïdora.")}
    %elif id_info.adjust_reason == '98':
        %if col:
            ${_(u"(2) Aquesta energia utilitzada inclou els ajustos corresponents a l'energia autoconsumida.")}
        %else:
            ${_(u"(2) Aquesta energia utilitzada inclou els ajustos corresponents al balanç horari ")}
            %if id_info.lang == 'ca_ES':
                <a href="https://ca.support.somenergia.coop/article/849-autoproduccio-que-es-el-balanc-net-horari">${_(u"(més informació).")}</a>
            %else:
                <a href="https://es.support.somenergia.coop/article/850-autoproduccion-que-es-el-balance-neto-horario">${_(u"(més informació).")}</a>
            %endif
        %endif
        <br>
    %elif id_info.adjust_reason == '97':
        ${_(u"(2) Aquesta energia utilitzada inclou ajustos perquè les lectures informades per la companyia distribuïdora no concorden amb els consums informats per a cada període.")}
    %endif
    <br>
    ${_(u"Si vols conèixer el detall de les teves dades horàries d’ús d’electricitat i de potència i disposes d’un comptador amb la telegestió activada, t’animem a registrar-te i accedir gratuïtament al portal web de la teva empresa distribuïdora: ")}
    %if id_info.has_web:
        <a href="${id_info.web_distri}">${id_info.web_distri}</a>
    %else:
        <i>${_(u"(Ho sentim, %s encara no ens ha facilitat l’enllaç al portal)") % id_info.distri_name }</i>
    %endif
</td>
</tr>
</table>
