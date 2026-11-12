<%page args="id" />
<%import locale
first_pass = True
%>
% if id.is_visible:
% for lines_data in id.lines_data:
    <tr>
    % if first_pass:
        <td class="td_second concepte_td" rowspan=${id.header_multi}>${_(u"Peatges")}</td>
        <%first_pass = False%>
    % endif
        <td class="detall_td">${_(u"Preu peatges per electricitat utilitzada [€/kWh]")}</td>
        % for p in id.showing_periods:
            % if p in lines_data:
                <td>${_(u"%s") %(formatLang(lines_data[p]["tolls_price_unit"], digits=6))}</td>
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
        <td class="detall_td">${_(u"kWh x €/kWh x (%s/%s) dies (del %s al %s)") % (lines_data.days, lines_data.days_per_year, lines_data.date_from, lines_data.date_to)}</td>
        % for p in id.showing_periods:
            % if p in lines_data:
                <td>${_(u"%s €") %(formatLang(lines_data[p]["tolls"]))}</td>
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
