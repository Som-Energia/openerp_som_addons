<%page args="id" />
<%import locale
first_pass = True
count = 1
%>
% if id.is_visible:
    % for generation_lines_data in id.generation_lines_data:
        <tr>
            % if first_pass:
                <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Compensació per electricitat excedentària")}</td>
                <%first_pass = False%>
            % endif
            <td class="td_bold detall_td">${_(u"Electricitat excedentària [kWh]")}</td>
            % for p in id.showing_periods:
                % if p in generation_lines_data:
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(generation_lines_data[p]["quantity"], digits=3))))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
            <td></td>
            <%count += 1%>
        </tr>
        <tr>
            <td class="td_bold detall_td">${_(u"Preu energia [€/kWh]")}</td>
            % for p in id.showing_periods:
                % if p in generation_lines_data:
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(generation_lines_data[p]["price_unit_multi"], digits=6))))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
            <td></td>
            <%count += 1%>
        </tr>
        % if count < id.header_multi:
        <tr class="tr_bold">
        % else:
        <tr class="tr_bold last_row">
        % endif
            <td class="detall_td">${_(u"kWh x €/kWh (del %s al %s)") % (generation_lines_data['date_from'], generation_lines_data['date_to'])}</td>
            % for p in id.showing_periods:
                % if p in generation_lines_data:
                    <td>${_(u"%s €") %(locale.str(locale.atof(formatLang(generation_lines_data[p]["price_subtotal"], digits=3))))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
            <td><span class="subtotal">${_(u"%s €") %(formatLang(generation_lines_data["total"]))}<sup>(1)</td>
            <%count += 1%>
        </tr>
    % endfor
    % if id.is_ajustment_visible:
        <tr class="last_row">
            <td class="detall_td">${_(u"Ajust límit de compensació per autoconsum")}</td>
            % for p in id.showing_periods:
                <td></td>
            % endfor
            <td><span class="subtotal">${_(u"%s €") %(formatLang(id.ajustment))}</span></td>
        </tr>
    % endif
% endif