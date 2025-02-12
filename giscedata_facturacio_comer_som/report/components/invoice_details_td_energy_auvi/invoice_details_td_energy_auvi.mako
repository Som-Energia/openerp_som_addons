<%page args="id" />
<%import locale%>

% for auvi_energy_line_data in id.auvi_energy_lines_data:
    <tr>
        % if auvi_energy_line_data.get('has_discount', False):
            <td class="detall_td">${_(u"Electricitat AV utilitzada [kWh] (real)") }<p class="detall_td_no_bold">${_(u"subjectes a descompte")}</p></td>
        % else:
            <td class="detall_td">${_(u"Electricitat AV utilitzada [kWh] (real)") }</td>
        % endif
        % for p in id.showing_periods:
            <% pAuvi = "Linia energia autoconsumida " + p %>
            % if pAuvi in auvi_energy_line_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(auvi_energy_line_data[pAuvi]["quantity"], digits=3))))}</td>
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
        <td class="detall_td">${_(u"Preu energia AV [€/kWh]")}</td>
        % for p in id.showing_periods:
            <% pAuvi = "Linia energia autoconsumida " + p %>
            % if pAuvi in auvi_energy_line_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(auvi_energy_line_data[pAuvi]["price_unit_multi"], digits=6))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
    ## <tr class="tr_bold">
    ##     <td class="detall_td">${_(u"kWh x €/kWh (del %s al %s)") % (energy_lines_data.date_from, energy_lines_data.date_to)}</td>
    ##     % for p in id.showing_periods:
    ##         <% pGwh = p + " GkWh" %>
    ##         % if pGwh in energy_lines_data:
    ##             <td>${_(u"%s €") %(formatLang(energy_lines_data[pGwh]["price_subtotal"]))}</td>
    ##         % else:
    ##             <td></td>
    ##         % endif
    ##     % endfor
    ##     <td><span class="subtotal">${_(u"%s €") %(formatLang(energy_lines_data.total))}</span></td>
    ##     % if id.iva_column:
    ##         <td>${_(u"%s") % (energy_lines_data.iva) }</td>
    ##     % endif
    ## </tr>
% endfor
