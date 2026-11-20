<%page args="adjustment_services, showing_periods, iva_column, description_colspan" />
<tr class="tr_bold">
    <td class="detall_td" colspan="${description_colspan}">
        % if adjustment_services.get('is_generation_adjustment'):
            ${_(u"Serveis d'Ajust segons preu REE pel periode facturat, aplicat a assignació GenerationkWh")}
        % else:
            ${_(u"Serveis d'Ajust segons preu REE pel periode facturat")}
        % endif
    </td>
    % for p in showing_periods:
            <td></td>
    % endfor
    <td><span class="subtotal">${_(u"%s €") % (formatLang(adjustment_services.total))}<sup class="sup_bold">(2)</sup></span></td>
    % if iva_column:
        <td>${_(u"%s") % (adjustment_services.iva) }</td>
    % endif
</tr>
