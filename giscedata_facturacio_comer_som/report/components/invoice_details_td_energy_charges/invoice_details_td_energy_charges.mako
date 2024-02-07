<%page args="id" />
<%import locale%>
<tr>
    <td class="td_third concepte_td" rowspan=${id.header_multi}>${_(u"Càrrecs")}</td>
    <td class="td_bold detall_td">${_(u"Preu càrrecs per electricitat utilitzades [€/kWh]")}</td>
    % for p in id.showing_periods:
        % if p in id and "preu_cargos" in id[p]:
            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_cargos"], digits=6))))}</td>
        % else:
            <td></td>
        % endif
    % endfor
    <td></td>
    % if id.iva_column:
        <td></td>
    % endif
</tr>
<tr class="${'last_row' if id.header_multi == 2 else ''}">
    <td class="td_bold detall_td">${_(u"kWh x €/kWh")}</td>
    % for p in id.showing_periods:
        % if p in id and "atr_cargos" in id[p]:
            <td>${_(u"%s €") %(formatLang(id[p]["atr_cargos"]))}</td>
        % else:
            <td></td>
        % endif
    % endfor
    <td></td>
    % if id.iva_column:
        <td></td>
    % endif
</tr>
