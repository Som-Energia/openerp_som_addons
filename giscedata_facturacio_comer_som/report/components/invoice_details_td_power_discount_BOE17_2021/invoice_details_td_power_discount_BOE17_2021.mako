<%page args="id" />
<%import locale %>
% if id.is_visible:
    <tr>
        <td class="td_bold detall_td">${_(u"Descompte sobre els càrrecs (RDL 17/2021) [€/kW i any]")}</td>
        % if len(id.showing_periods) == 3:
            % for p in id.showing_periods[:-1]:
                % if p in id and "price_unit" in id[p]:
                    % if p == 'P1':
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["price_unit"], digits=6))))}</td>
                        <td></td>
                    % else:
                        <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["price_unit"], digits=6))))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
        % else:
            % for p in id.showing_periods:
                % if p in id and "price_unit" in id[p]:
                    <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["price_unit"], digits=6))))}</td>
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
    <tr class="${'' if id.is_indexed else 'tr_bold'} last_row">
        <td class="detall_td">${_(u"kW x €/kW x (%s/%s) dies") % (id.dies, id.dies_any)}</td>
        % if len(id.showing_periods) == 3:
            % for p in id.showing_periods[:-1]:
                % if p in id and "price_subtotal" in id[p]:
                    % if p == 'P1':
                        <td>${_(u"%s €") %(formatLang(id[p]["price_subtotal"]))}</td>
                        <td></td>
                    % else:
                        <td>${_(u"%s €") %(formatLang(id[p]["price_subtotal"]))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
        % else:
            % for p in id.showing_periods:
                % if p in id and "price_subtotal" in id[p]:
                    <td>${_(u"%s €") %(formatLang(id[p]["price_subtotal"]))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
        % endif
        <td>
        % if not id.is_indexed:
            <span class="subtotal">${_(u"%s €") %(formatLang(id.total))}</span>
        % endif
        </td>
        % if id.iva_column:
            <td>${_(u"%s") % (id.iva) }</td>
        % endif
    </tr>
% endif
