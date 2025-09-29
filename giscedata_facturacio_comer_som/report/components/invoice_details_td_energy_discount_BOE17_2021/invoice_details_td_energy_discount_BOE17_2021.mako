<%page args="id" />
<%import locale %>
% if id.is_visible:
    <tr>
        <td class="td_bold detall_td">${_(u"Descompte sobre els càrrecs (RDL 17/2021) [€/kWh]")}</td>
        % for p in id.showing_periods:
            % if p in id and "price_unit" in id[p]:
                <td>${_(u"%s") %(locale.str(locale.atof(formatLang(id[p]["price_unit"], digits=6))))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
    <tr class="${'' if id.is_indexed else 'tr_bold'} last_row">
        <td class="detall_td">${_(u"kWh x €/kWh")}</td>
        % for p in id.showing_periods:
            % if p in id and "price_subtotal" in id[p]:
                <td>${_(u"%s €") %(formatLang(id[p]["price_subtotal"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
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
