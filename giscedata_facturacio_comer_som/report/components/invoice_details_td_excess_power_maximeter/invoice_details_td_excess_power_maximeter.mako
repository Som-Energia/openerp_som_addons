<%page args="id" />
<%import locale
first_pass = True
count = 1
%>

% if id.is_visible:
    % for excess_data in id.excess_data:
        % if len(id.showing_periods) == 3:
            <tr>
                % if first_pass:
                    <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Facturacio per excés de potència")}</td>
                    <%first_pass = False%>
                % endif
                <td class="td_bold detall_td">${_(u"Potència maxímetre [kW]")}</td>
                % for p in id.showing_periods[:-1]:
                    % if p in excess_data:
                        % if p == 'P1':
                            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["power_maximeter"], digits=3))))}</td>
                            <td></td>
                        % else:
                            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["power_maximeter"], digits=3))))}</td>
                        % endif
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
                % if id.iva_column:
                    <td></td>
                % endif
                <%count += 1%>
            </tr>
            <tr>
                % if excess_data["pre_2025_04_01"]:
                    <td class="td_bold detall_td">${_(u"2 x (Potència maxímetre - Potència contractada) [kW]")}</td>
                % else:
                    <td class="td_bold detall_td">${_(u"Potència maxímetre - Potència contractada [kW]")}</td>
                % endif
                % for p in id.showing_periods[:-1]:
                    % if p in excess_data:
                        % if p == 'P1':
                            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["power_excess"], digits=3))))}</td>
                            <td></td>
                        % else:
                            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["power_excess"], digits=3))))}</td>
                        % endif
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
                % if id.iva_column:
                    <td></td>
                % endif
                <%count += 1%>
            </tr>
            <tr>
                % if excess_data['multi'] > 1:
                    <td class="td_bold detall_td">${_(u"Preu excés potència [€/kW i dia]")}</td>
                % else:
                    <td class="td_bold detall_td">${_(u"Preu excés potència [€/kW i mes]")}</td>
                % endif
                % for p in id.showing_periods[:-1]:
                    % if p in excess_data:
                        % if p == 'P1':
                            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["price_excess"], digits=6))))}</td>
                            <td></td>
                        % else:
                            <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["price_excess"], digits=6))))}</td>
                        % endif
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
                % if id.iva_column:
                    <td></td>
                % endif
                <%count += 1%>
            </tr>
            % if count < id.header_multi:
            <tr class="tr_bold">
            % else:
            <tr class="tr_bold last_row">
            % endif
                % if excess_data['multi'] > 1:
                    <td class="detall_td">${_(u"kW x €/kW x %s dies (del %s al %s)") %(int(excess_data['multi']),excess_data['date_from'], excess_data['date_to'])}</td>
                % else:
                    <td class="detall_td">${_(u"kW x €/kW")}</td>
                % endif
                % for p in id.showing_periods[:-1]:
                    % if p in excess_data:
                        % if p == 'P1':
                            <td>${_(u"%s €") %(formatLang(excess_data[p]["price_subtotal"]))}</td>
                            <td></td>
                        % else:
                            <td>${_(u"%s €") %(formatLang(excess_data[p]["price_subtotal"]))}</td>
                        % endif
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td><span class="subtotal">${_(u"%s €") %(formatLang(excess_data['total']))}</span></td>
                % if id.iva_column:
                    <td>${_(u"%s") % (excess_data['iva']) }</td>
                % endif
                <%count += 1%>
            </tr>
        % else:
            <tr>
                % if first_pass:
                    <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Facturacio per excés de potència")}</td>
                    <%first_pass = False%>
                % endif
                <td class="td_bold detall_td">${_(u"Potència maxímetre [kW]")}</td>
                % for p in id.showing_periods:
                    % if p in excess_data:
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["power_maximeter"], digits=3))))}</td>
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
                % if id.iva_column:
                    <td></td>
                % endif
                <%count += 1%>
            </tr>
            <tr>
                % if excess_data["pre_2025_04_01"]:
                    <td class="td_bold detall_td">${_(u"2 x (Potència maxímetre - Potència contractada) [kW]")}</td>
                % else:
                    <td class="td_bold detall_td">${_(u"Potència maxímetre - Potència contractada [kW]")}</td>
                % endif
                % for p in id.showing_periods:
                    % if p in excess_data:
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["power_excess"], digits=3))))}</td>
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
                % if id.iva_column:
                    <td></td>
                % endif
                <%count += 1%>
            </tr>
            <tr>
                % if excess_data['multi'] > 1:
                    <td class="td_bold detall_td">${_(u"Preu excés potència [€/kW i dia]")}</td>
                % else:
                    <td class="td_bold detall_td">${_(u"Preu excés potència [€/kW i mes]")}</td>
                % endif
                % for p in id.showing_periods:
                    % if p in excess_data:
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(excess_data[p]["price_excess"], digits=6))))}</td>
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
                % if id.iva_column:
                    <td></td>
                % endif
                <%count += 1%>
            </tr>
            % if count < id.header_multi:
            <tr class="tr_bold">
            % else:
            <tr class="tr_bold last_row">
            % endif
                % if excess_data['multi'] > 1:
                    <td class="detall_td">${_(u"kW x €/kW x %s dies (del %s al %s)") %(int(excess_data['multi']),excess_data['date_from'], excess_data['date_to'])}</td>
                % else:
                    <td class="detall_td">${_(u"kW x €/kW x (%.f/%d) dies (del %s al %s)") %(int(excess_data['multi']*id.days), id.days,excess_data['date_from'], excess_data['date_to'])}</td>
                % endif
                % for p in id.showing_periods:
                    % if p in excess_data:
                        <td>${_(u"%s €") %(formatLang(excess_data[p]["price_subtotal"]))}</td>
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td><span class="subtotal">${_(u"%s €") %(formatLang(excess_data['total']))}</span></td>
                % if id.iva_column:
                    <td>${_(u"%s") % (excess_data['iva']) }</td>
                % endif
                <%count += 1%>
            </tr>
        % endif
    % endfor
% endif
