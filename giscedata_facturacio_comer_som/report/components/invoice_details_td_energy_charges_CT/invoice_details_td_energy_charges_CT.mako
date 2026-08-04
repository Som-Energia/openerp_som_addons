<%page args="id" />
<%import locale
first_pass = True
%>
% if id.is_visible:
% for lines_data in id.lines_data:
    <tr>
    % if first_pass:
        <td class="td_third concepte_td" rowspan=${id.header_multi}>${_(u"Càrrecs")}</td>
        <%first_pass = False%>
    % endif
        <td class="detall_td">${_(u"Preu càrrecs per electricitat utilitzades [€/kWh]")}</td>
        % for p in id.showing_periods:
            % if p in lines_data:
                <td>${_(u"%s") %(formatLang(lines_data[p]["preu_cargos"], digits=6))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
    <tr class="${'last_row' if id.lines_data[-1] == lines_data else ''}">
        <td class="detall_td">${_(u"kWh x €/kWh x (%s/%s) dies (del %s al %s)") % (lines_data.days, lines_data.days_per_year, lines_data.date_from, lines_data.date_to)}</td>
        % for p in id.showing_periods:
            % if p in lines_data:
                <td>${_(u"%s €") %(formatLang(lines_data[p]["atr_cargos"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
% endfor
% endif
