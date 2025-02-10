<%page args="bs" />
%if bs.is_visible:
<%
import locale
first_pass = True
%>
% for l in bs.lines:
    <tr class="tr_bold ${'last_row' if bs.lines[-1] == l else ''}">
        % if first_pass:
            <td class="td_first concepte_td" rowspan=${bs.header_multi}>${_(u"Bo social")}</td>
            <%first_pass = False%>
        % endif
            <td class="detall_td" colspan="${bs.number_of_columns}">${_(u"%s dies x %s €/dia") % (int(l['days']), locale.str(locale.atof(formatLang(l['price_per_day'], digits=6))))}</td>
            <td class="subtotal">${_(u"%s €") % formatLang(l['subtotal'])}</td>
            % if bs.iva_column:
                <td>${_(u"%s") % (l['iva']) }</td>
            % endif
    </tr>
% endfor
%endif
