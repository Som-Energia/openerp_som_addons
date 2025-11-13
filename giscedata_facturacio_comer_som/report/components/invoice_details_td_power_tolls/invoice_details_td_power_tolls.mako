<%page args="id" />
<%import locale %>
% if 'P1' in id:
<tr>
    <td class="td_second concepte_td" rowspan="2">${_(u"Peatges")}</td>
    <td class="td_bold detall_td">${_(u"Preu peatges per potència contractada [€/kW i any]")}</td>
    % if len(id.showing_periods) == 3:
        % for p in id.showing_periods[:-1]:
            % if p in id and id[p]["preu_peatge"]:
                % if p == 'P1':
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_peatge"], digits=6))))}</td>
                    <td></td>
                % else:
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_peatge"], digits=6))))}</td>
                % endif
            % else:
                <td></td>
            % endif
        % endfor
    % else:
        % for p in id.showing_periods:
            % if p in id and id[p]["preu_peatge"]:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_peatge"], digits=6))))}</td>
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
    <td class="td_bold detall_td">${_(u"kW x €/kW x (%s/%s) dies") % (id.dies, id.dies_any)}</td>
    % if len(id.showing_periods) == 3:
        % for p in id.showing_periods[:-1]:
            % if p in id and id[p]["atr_peatge"]:
                % if p == 'P1':
                    <td>${_(u"%s €") %(formatLang(id[p]["atr_peatge"]))}</td>
                    <td></td>
                % else:
                    <td>${_(u"%s €") %(formatLang(id[p]["atr_peatge"]))}</td>
                % endif
            % else:
                <td></td>
            % endif
        % endfor
    % else:
        % for p in id.showing_periods:
            % if p in id and id[p]["atr_peatge"]:
                <td>${_(u"%s €") %(formatLang(id[p]["atr_peatge"]))}</td>
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
% endif
