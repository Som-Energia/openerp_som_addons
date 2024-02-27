<%page args="fs" />
%if fs.is_visible:
<%
import locale
%>
    <tr class="tr_bold last_row">
        <td class="td_first concepte_td">${_(u"Flux Solar")}</td>
        <td class="detall_td" colspan="${fs.number_of_columns}">${_(u"Descompte per Flux Solar")}</td>
        <td class="subtotal">${_(u"%s €") % formatLang(fs.subtotal)}</td>
        % if fs.iva_column:
            <td>${_(u"%s") % (fs.iva) }</td>
        % endif
    </tr>
%endif
