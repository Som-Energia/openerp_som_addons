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
        <td class="detall_td">${_(u"Preu peatges per potència contractada [€/kW i any]")}</td>
        % if len(id.showing_periods) == 3:
            % for p in id.showing_periods[:-1]:
                % if p in lines_data and lines_data[p]["calculated_tolls"]:
                    % if p == 'P1':
                        <td>${_(u"%s") %(formatLang(lines_data[p]["calculated_tolls"], digits=5))}</td>
                        <td></td>
                    % else:
                        <td>${_(u"%s") %(formatLang(lines_data[p]["calculated_tolls"], digits=6))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
        % else:
            % for p in id.showing_periods:
                % if p in lines_data and lines_data[p]["calculated_tolls"]:
                    <td>${_(u"%s") %(formatLang(lines_data[p]["calculated_tolls"], digits=6))}</td>
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
        <td class="detall_td">${_(u"kW x €/kW x (%s/%s) dies (del %s al %s)") % (lines_data.days, lines_data.days_per_year, lines_data.date_from, lines_data.date_to)}</td>
        % if len(id.showing_periods) == 3:
            % for p in id.showing_periods[:-1]:
                % if p in lines_data and lines_data[p]["tolls"]:
                    % if p == 'P1':
                        <td>${_(u"%s €") %(formatLang(lines_data[p]["tolls"]))}</td>
                        <td></td>
                    % else:
                        <td>${_(u"%s €") %(formatLang(lines_data[p]["tolls"]))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
        % else:
            % for p in id.showing_periods:
                % if p in lines_data and lines_data[p]["tolls"]:
                    <td>${_(u"%s €") %(formatLang(lines_data[p]["tolls"]))}</td>
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
% endfor
% endif
