<%page args="id" />
<%import locale%>

% for energy_lines_data in id.gkwh_energy_lines_data:
    <tr>
        % if energy_lines_data.get('has_discount', False):
            <td class="detall_td">${_(u"Electricitat GenerationkWh utilitzada [kWh]")}<p class="detall_td_no_bold">${_(u"subjectes a descompte")}</p></td>
        % else:
            <td class="detall_td">${_(u"Electricitat GenerationkWh utilitzada [kWh]")}</td>
        % endif
        % for p in id.showing_periods:
            <% pGwh = p + " GkWh" %>
            % if pGwh in energy_lines_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(energy_lines_data[pGwh]["quantity"], digits=3))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr>
        <td class="detall_td">${_(u"Preu GenerationkWh [€/kWh]")}</td>
        % for p in id.showing_periods:
            <% pGwh = p + " GkWh" %>
            % if pGwh in energy_lines_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(energy_lines_data[pGwh]["price_unit_multi"], digits=6))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr class="tr_bold">
        <td class="detall_td">${_(u"kWh x €/kWh")}</td>
        % for p in id.showing_periods:
            <% pGwh = p + " GkWh" %>
            % if pGwh in energy_lines_data:
                <td>${_(u"%s €") %(formatLang(energy_lines_data[pGwh]["price_subtotal"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td><span class="subtotal">${_(u"%s €") %(formatLang(energy_lines_data.total))}</span></td>
    </tr>
% endfor