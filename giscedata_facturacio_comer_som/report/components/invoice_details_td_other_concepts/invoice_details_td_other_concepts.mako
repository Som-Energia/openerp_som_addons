<%page args="id" />
<%
import locale
first_pass = True
%>
% for l in id.bosocial_lines:
    <tr class= "${'last_row' if id.last_row == 'bosocial' else ''}">
        % if first_pass:
            <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Altres conceptes")}</td>
            <%first_pass = False%>
        % endif
        <td class="detall_td" colspan="${id.number_of_columns}">${_(u"Bo social (RD 7/2016 23 desembre) %s dies x %s €/dia") % (int(l['quantity']), locale.str(locale.atof(formatLang(l['price_unit'], digits=3))))}</td>
        <td class="subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</td>
        % if id.iva_column:
            <td class="detall_td periods_td">${_(u"%s") % (l['iva']) }</td>
        % endif
    </tr>
% endfor
% for l in id.altres_lines:
    <tr class= "${'last_row' if id.last_row == 'altres' else ''}">
        % if first_pass:
            <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Altres conceptes")}</td>
            <%first_pass = False%>
        % endif
        <td class="detall_td" colspan="${id.number_of_columns}">${l['name']}</td>
        <td class="subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</td>
        % if id.iva_column:
            <td class="detall_td periods_td">${_(u"%s") % (l['iva']) }</td>
        % endif
    </tr>
% endfor
% for l in id.donatiu_lines:
    <tr class= "${'last_row' if id.last_row == 'donatiu' else ''}">
        % if first_pass:
            <td class="td_first concepte_td" rowspan="${id.header_multi}">${_(u"Altres conceptes")}</td>
            <%first_pass = False%>
        % endif
        <td class="detall_td" colspan="${id.number_of_columns}">${_(u"Donatiu voluntari (exempt d'IVA) %s kWh x %s €/kWh") % (formatLang(l['quantity']), formatLang(l['price_unit_multi']))}</td>
        <td class="subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
% endfor
% for l in id.iese_lines:
    <tr>
        % if id.fiscal_position:
            <td class="td_first concepte_td">${_(u"Impost de l'electricitat")}</td>
            <td class="detall_td" colspan="${id.number_of_columns}">
                % if l.tax_type == '0.5percent':
                    ${_(u"%s € x 0,5%%") % (formatLang(l['base_iese']))}
                    ${_(u"En virtut del Reial Decret-llei 17/2021, del 14 de setembre, l'impost especial sobre l'electricitat aplicable a la factura es troba reduït del 5,11269632% al 0,5%.")}
                % elif l.tax_type == '2.5percent':
                    ${_(u"%s € x 2,5%%") % (formatLang(l['base_iese']))}
                    ${_(u"En virtut del Reial Decret-llei 8/2023, del 27 de desembre, l'impost especial sobre l'electricitat aplicable a la factura es troba reduït del 5,11269632% al 2,5%.")}
                % elif l.tax_type == '3.8percent':
                    ${_(u"%s € x 3,8%%") % (formatLang(l['base_iese']))}
                    ${_(u"En virtut del Reial Decret-llei 8/2023, del 27 de desembre, l'impost especial sobre l'electricitat aplicable a la factura es troba reduït del 5,11269632% al 3,8%.")}
                % elif l.tax_type == '1euroMWh':
                    ${_(u"%s kWh x 0,001 €/kWh (aplicant Art 99.2 de la Llei 28/2014 sense bonificació del 85%%)") % (formatLang(l['base_iese']))}
                % elif l.tax_type == '0.5euroMWh':
                    ${_(u"%s kWh x 0,0005 €/kWh (aplicant Art 99.2 de la Llei 28/2014 sense bonificació del 85%%)") % (formatLang(l['base_iese']))}
                % elif l.tax_type == 'excempcio':
                    ${_(u"%s € x 0,5%%") % (formatLang(l['base_iese']))}
                % else:
                    ${_(u"%s € x 5,11269%%") % (formatLang(l['base_iese']))}
                % endif
                % if  l.tax_type in ('excempcio', '5.11percent'):
                    %if id.is_excempcio_IE_base:
                        ${_(u" (amb l'exempció del {}% sobre el {}% de Base Imposable IE)").format(
                            id.percentatges_exempcio_splitted[2].replace('-', ''),
                            formatLang(id.percentatges_exempcio[0] * 100, digits=1)
                        )}
                    %else:
                        ${_(u" (amb l'exempció del ")} ${id.excempcio})
                    %endif
                % endif
            </td>
            <td class="subtotal">${_(u"%s €") % formatLang(l['tax_amount'])}</td>
            % if id.iva_column:
                <td class="detall_td">${_(u"%s") % (l['iva']) }</td>
            % endif
        % else:
            <td class="td_first concepte_td">${_(u"Impost de l'electricitat")}</td>
            <td class="detall_td" colspan="${id.number_of_columns}">
                % if l.tax_type == '0.5percent':
                    ${_(u"%s € x 0,5%%") % (formatLang(l['base_amount']))}
                    ${_(u"En virtut del Reial Decret-llei 17/2021, del 14 de setembre, l'impost especial sobre l'electricitat aplicable a la factura es troba reduït del 5,11269632% al 0,5%.")}
                % elif l.tax_type == '2.5percent':
                    ${_(u"%s € x 2,5%%") % (formatLang(l['base_amount']))}
                    ${_(u"En virtut del Reial Decret-llei 8/2023, del 27 de desembre, l'impost especial sobre l'electricitat aplicable a la factura es troba reduït del 5,11269632% al 2,5%.")}
                % elif l.tax_type == '3.8percent':
                    ${_(u"%s € x 3,8%%") % (formatLang(l['base_amount']))}
                    ${_(u"En virtut del Reial Decret-llei 8/2023, del 27 de desembre, l'impost especial sobre l'electricitat aplicable a la factura es troba reduït del 5,11269632% al 3,8%.")}
                % elif l.tax_type == '1euroMWh':
                    ${_(u"%s kWh x 0,001 €/kWh (aplicant Art 99.2 de la Llei 28/2014)") % (formatLang(l['base_amount']))}
                % elif l.tax_type == '0.5euroMWh':
                    ${_(u"%s kWh x 0,0005 €/kWh (aplicant Art 99.2 de la Llei 28/2014)") % (formatLang(l['base_amount']))}
                % else:
                    ${_(u"%s € x 5,11269%%") % (formatLang(l['base_amount']))}
                % endif
            </td>
            <td class="subtotal">${_(u"%s €") % formatLang(l['tax_amount'])}</td>
            % if id.iva_column:
                <td class="detall_td periods_td">${_(u"%s") % (l['iva']) }</td>
            % endif
        % endif
    </tr>
% endfor
% for l in id.lloguer_lines:
    <tr>
        <td class="td_first concepte_td">${_(u"Lloguer de comptador")}</td>
        <td class="detall_td" colspan="${id.number_of_columns}">${_(u"%s dies x %s €/dia") % (int(l['quantity']), locale.str(locale.atof(formatLang(l['price_unit'], digits=6))))}</td>
        <td class="subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</td>
        % if id.iva_column:
            <td class="detall_td periods_td">${_(u"%s") % (l['iva']) }</td>
        % endif
    </tr>
% endfor
% for l in id.iva_lines:
    <tr>
        <td class="td_first concepte_td">${l['name']}</td>
        <td class="detall_td" colspan="${id.number_of_columns}">${_(u"%s € ") % (formatLang(l['base']))}${_(u"(BASE IMPOSABLE)")}
        %if l.disclaimer_21_to_5:
            ${_(u"En virtut del Reial Decret-llei 12/2021, del 24 de juny, l'IVA aplicable a la factura es troba reduït del 21% al 5%.")}
        %elif l.disclaimer_21_to_10:
            ${_(u"En virtut del Reial Decret-llei 8/2023, del 27 de desembre, l’IVA aplicat a la factura es troba reduït del 21% al 10%")}
        %endif
        </td>
        <td class="subtotal">${_(u"%s €") % formatLang(l['amount'])}</td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
% endfor
% for l in id.igic_lines:
    <tr>
        <td class="td_first concepte_td">${l['name']}</td>
        <td class="detall_td" colspan="${id.number_of_columns}">${_(u"%s € ") % (formatLang(l['base']))}${_(u"(BASE IMPOSABLE)")}</td>
        <td class="subtotal">${_(u"%s €") % formatLang(l['amount'])}</td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
% endfor
