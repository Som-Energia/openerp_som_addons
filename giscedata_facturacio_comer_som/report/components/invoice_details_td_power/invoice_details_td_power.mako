<%page args="id" />
<%
import locale
first_pass = True
%>

% for power_lines_data in id.power_lines_data:
    <tr>
    % if first_pass:
        <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Facturació per potencia contractada")}</td>
        <%first_pass = False%>
    % endif
        <td class="detall_td">${_(u"Potència contractada [kW]")}</td>
        % if len(id.showing_periods) == 3:
            % for p in id.showing_periods[:-1]:
                % if p in power_lines_data:
                    % if p == 'P1':
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(power_lines_data[p]["quantity"], digits=3))))}</td>
                        <td></td>
                    % else:
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(power_lines_data[p]["quantity"], digits=3))))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
        % else:
            % for p in id.showing_periods:
                % if p in power_lines_data:
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(power_lines_data[p]["quantity"], digits=3))))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
        % endif
        <td></td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
    <tr>
        <td class="detall_td">${_(u"Preu potència contractada [€/kW i any]")}</td>
        % if len(id.showing_periods) == 3:
            % for p in id.showing_periods[:-1]:
                % if p in power_lines_data:
                    % if p == 'P1':
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(power_lines_data[p]["atr_price"], digits=6))))}</td>
                        <td></td>
                    % else:
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(power_lines_data[p]["atr_price"], digits=6))))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
        % else:
            % for p in id.showing_periods:
                % if p in power_lines_data:
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(power_lines_data[p]["atr_price"], digits=6))))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
        % endif
        <td></td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
    <tr class="tr_bold">
        <td class="detall_td">${_(u"kW x €/kW x (%.f/%d) dies (del %s al %s)") %(int(power_lines_data.multi), power_lines_data.days_per_year, power_lines_data.date_from, power_lines_data.date_to)}</td>
        % if len(id.showing_periods) == 3:
            % for p in id.showing_periods[:-1]:
                % if p in power_lines_data:
                    % if p == 'P1':
                        <td>${_(u"%s €") %(formatLang(power_lines_data[p]["price_subtotal"]))}</td>
                        <td></td>
                    % else:
                        <td>${_(u"%s €") %(formatLang(power_lines_data[p]["price_subtotal"]))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
        % else:
            % for p in id.showing_periods:
                % if p in power_lines_data:
                    <td>${_(u"%s €") %(formatLang(power_lines_data[p]["price_subtotal"]))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
        % endif
        <td><span class="subtotal">${_(u"%s €") %(formatLang(power_lines_data.total))}</span></td>
        % if id.iva_column:
            <td>${_(u"%s") % (power_lines_data.iva) }</td>
        % endif
    </tr>
% endfor
