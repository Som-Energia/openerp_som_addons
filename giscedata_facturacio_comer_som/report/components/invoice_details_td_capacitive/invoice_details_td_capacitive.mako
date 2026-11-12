<%page args="id" />
<%import locale
first_pass = True
%>

% if id.is_visible:
    <tr>
        % if first_pass:
            <td class="td_first concepte_td" rowspan="3">${_(u"Penalització energia reactiva capacitiva")}</td>
            <%first_pass = False%>
        % endif
        <td class="td_bold detall_td">${_(u"Energia reactiva capacitiva penalitzable [kVArh]")}</td>
        % for p in id.showing_periods:
            % if p in id.capacitive_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id.capacitive_data[p]["quantity"], digits=3))))}</td>
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
        <td class="td_bold detall_td">${_(u"Preu energia reactiva capacitiva [€/kVArh]")}</td>
        % for p in id.showing_periods:
            % if p in id.capacitive_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id.capacitive_data[p]["price_unit_multi"], digits=3))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
    <tr class="last_row tr_bold">
        <td class="detall_td">${_(u"kVArh x €/kVArh")}</td>
        % for p in id.showing_periods:
            % if p in id.capacitive_data:
                <td>${_(u"%s €") %(formatLang(id.capacitive_data[p]["price_subtotal"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td><span class="subtotal">${_(u"%s €") %(formatLang(id.capacitive_data.total))}</span></td>
        % if id.iva_column:
            <td>${_(u"%s") % (id.capacitive_data.iva) }</td>
        % endif
    </tr>
% endif
