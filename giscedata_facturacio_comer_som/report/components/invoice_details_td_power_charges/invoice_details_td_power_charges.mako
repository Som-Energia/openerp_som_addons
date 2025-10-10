<%page args="id" />
<%import locale %>
% if 'P1' in id:
<tr>
    <td class="td_third concepte_td" rowspan=${id.header_multi}>${_(u"Càrrecs")}</td>
    <td class="td_bold detall_td">${_(u"Preu càrrecs per potència contractada [€/kW i any]")}</td>
    % if len(id.showing_periods) == 3:
        % for p in id.showing_periods[:-1]:
            % if p in id and "preu_cargos" in id[p]:
                % if p == 'P1':
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_cargos"], digits=6))))}</td>
                    <td></td>
                % else:
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_cargos"], digits=6))))}</td>
                % endif
            % else:
                <td></td>
            % endif
        % endfor
    % else:
        % for p in id.showing_periods:
            % if p in id and "preu_cargos" in id[p]:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["preu_cargos"], digits=6))))}</td>
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
<tr class="${'last_row' if id.header_multi == 2 else ''}">
    <td class="td_bold detall_td">${_(u"kW x €/kW x (%s/%s) dies") % (id.dies, id.dies_any)}</td>
    % if len(id.showing_periods) == 3:
        % for p in id.showing_periods[:-1]:
            % if p in id and "atr_cargos" in id[p]:
                % if p == 'P1':
                    <td>${_(u"%s €") %(formatLang(id[p]["atr_cargos"]))}</td>
                    <td></td>
                % else:
                    <td>${_(u"%s €") %(formatLang(id[p]["atr_cargos"]))}</td>
                % endif
            % else:
                <td></td>
            % endif
        % endfor
    % else:
        % for p in id.showing_periods:
            % if p in id and "atr_cargos" in id[p]:
                <td>${_(u"%s €") %(formatLang(id[p]["atr_cargos"]))}</td>
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
