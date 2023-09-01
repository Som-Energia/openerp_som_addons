<%page args="fs" />
%if fs.is_visible:
<%
import locale
%>
    <tr class="last_row">
        <td class="td_first concepte_td">${_(u"Descompte per Flux Solar")}</td>
        <td class="detall_td" colspan="${fs.number_of_columns}"></td>
        <td class="subtotal">${_(u"%s €") % formatLang(fs.subtotal)}</td>
    </tr>
%endif