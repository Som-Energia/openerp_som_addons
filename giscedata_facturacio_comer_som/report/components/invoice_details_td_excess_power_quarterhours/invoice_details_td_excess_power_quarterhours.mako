<%page args="id" />
<%import locale
first_pass = True
%>

% if id.is_visible:
    % for excess_data in id.excess_data:
    <tr>
        % if first_pass:
            <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Facturacio per excés de potència")}</td>
            <%first_pass = False%>
        % endif
        <td class="td_bold detall_td">${_(u"Potència excés [kW]")}</td>
        % for p in id.showing_periods:
            % if p in id.excess_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id.excess_data[p]["power_excess"], digits=3))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr>
        % if excess_data['visible_days_month']:
            <td class="td_bold detall_td">${_(u"Preu potència excés [€/kW i mes]")}</td>
        % else:
            <td class="td_bold detall_td">${_(u"Preu potència excés [€/kW]")}</td>
        % endif
        % for p in id.showing_periods:
            % if p in id.excess_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id.excess_data[p]["price_excess"], digits=6))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr>
        <td class="td_bold detall_td">${_(u"Coeficient kp")}</td>
        % for p in id.showing_periods:
            % if p in id.excess_data:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id.excess_data[p]["kp"], digits=6))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr class="tr_bold last_row">
        % if excess_data['visible_days_month']:
            <td class="detall_td">${_(u"kW excés x €/kW excés x kp x (%.f/30) dies") %(int(id.days))}</td>
        % else:
            <td class="detall_td">${_(u"kW excés x €/kW excés x kp")}</td>
        % endif
        % for p in id.showing_periods:
            % if p in id.excess_data:
                <td>${_(u"%s €") %(formatLang(id.excess_data[p]["price_subtotal"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td><span class="subtotal">${_(u"%s €") %(formatLang(id.total))}</span></td>
    </tr>
    %endfor
% endif