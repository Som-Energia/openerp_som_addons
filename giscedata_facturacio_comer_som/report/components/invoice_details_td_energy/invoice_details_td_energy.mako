<%page args="id" />
<%import locale
first_pass = True
first_energy_line = True
%>
% if False:
    ${_(u"sense lectura")}
% endif
% for energy_lines_data in id.energy_lines_data:
    <tr>
    % if first_pass:
        <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Facturació per electricitat utilitzada")}</td>
        <%first_pass = False%>
    % endif
        % if first_energy_line:
            % if energy_lines_data.get('has_discount', False):
                <td class="detall_td">${_(u"Electricitat utilitzada [kWh] (%s)") % (_(energy_lines_data.origin))}<p class="detall_td_no_bold">${_(u"subjectes a descompte")}</p></td>
            % else:
                <td class="detall_td">${_(u"Electricitat utilitzada [kWh] (%s)") % (_(energy_lines_data.origin))}</td>
            % endif
            <%first_energy_line = False%>
        % else:
            % if energy_lines_data.get('has_discount', False):
                <td class="detall_td">${_(u"Electricitat utilitzada [kWh]")}<p class="detall_td_no_bold">${_(u"subjectes a descompte")}</p></td>
            % else:
                <td class="detall_td">${_(u"Electricitat utilitzada [kWh]")}</td>
            % endif
        % endif
        % for p in id.showing_periods:
            % if p in energy_lines_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(energy_lines_data[p]["quantity"], digits=3))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr>
        <td class="detall_td">${_(u"Preu energia [€/kWh]")}</td>
        % for p in id.showing_periods:
            % if p in energy_lines_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(energy_lines_data[p]["price_unit_multi"], digits=6))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr class="tr_bold">
        <td class="detall_td">${_(u"kWh x €/kWh (del %s al %s)") % (energy_lines_data.date_from, energy_lines_data.date_to)}</td>
        % for p in id.showing_periods:
            % if p in energy_lines_data:
                <td>${_(u"%s €") %(formatLang(energy_lines_data[p]["price_subtotal"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td><span class="subtotal">${_(u"%s €") %(formatLang(energy_lines_data.total))}</span></td>
    </tr>
% endfor
% if id.maj_line_data:
    <tr class="tr_bold">
        <td class="detall_td">
            ${_(u"Import Ajust mecanisme gas RDL 10/2022 (%s kWh x %s €/kWh) (del %s al %s)") % (
                locale.str(locale.atof(formatLang(id.maj_line_data.quantity, digits=3))),
                locale.str(locale.atof(formatLang(id.maj_line_data.price, digist=6))),
                id.maj_line_data.date_from,
                id.maj_line_data.date_to
            )}
        </td>
        % for p in id.showing_periods:
                <td></td>
        % endfor
        <td><span class="subtotal">${_(u"%s €") % (formatLang(id.maj_line_data.total))}</span></td>
    </tr>
