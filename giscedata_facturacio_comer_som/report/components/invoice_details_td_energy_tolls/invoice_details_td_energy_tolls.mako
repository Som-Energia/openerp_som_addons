<%page args="id" />
<%import locale%>
<tr>
    <td class="td_second concepte_td" rowspan="2">${_(u"Peatges")}</td>
    <td class="td_bold detall_td">${_(u"Preu peatges per electricitat utilitzada [€/kWh]")}</td>
    % for p in id.showing_periods:
        % if p in id:
            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_peatge"], digits=6))))}</td>
        % else:
            <td></td>
        % endif
    % endfor
    <td></td>
    % if id.iva_column:
        <td></td>
    % endif
</tr>
<tr>
    <td class="td_bold detall_td">${_(u"kWh x €/kWh")}</td>
    % for p in id.showing_periods:
        % if p in id:
            <td>${_(u"%s €") %(locale.str(locale.atof(formatLang(id[p]["atr_peatge"], digits=6))))}</td>
        % else:
            <td></td>
        % endif
    % endfor
    <td></td>
    % if id.iva_column:
        <td></td>
    % endif
</tr>
