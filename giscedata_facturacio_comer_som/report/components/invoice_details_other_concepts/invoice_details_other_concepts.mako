<%page args="id_other" />
<style>
<%include file="invoice_details_other_concepts.css" />
</style>
<% import locale %>
    <!-- ALTRES -->
    <p>${_(u"A aquests imports hauràs de sumar els altres costos que detallem a continuació:")}<br /></p>
    % for l in id_other.bosocial_lines:
    <div class="detail_line">
        <div class="detail_description_line">${_(u"Bo social (RD 7/2016 23 desembre)")}</div>
        <div class="detail_description_line">${_(u"%s dies x %s €/dia") % (int(l['quantity']), locale.str(locale.atof(formatLang(l['price_unit'], digits=3))))}</div>
        <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</div>
    </div>
    % endfor
    % for l in id_other.iese_lines:
    <div class="detail_line">
        % if id_other.fiscal_position:
            <div class="detail_description_line">${_(u"Impost d'electricitat")}</div>
            <div style="font-weight: bold; float:left; width: 45em;">
                ${(_(u"%s x 5,11269%%") % (formatLang(l['base_iese'])))}
                %if id_other.is_excempcio_IE_base:
                    ${_(u" (amb l'exempció del {} sobre el {}% de Base Imposable IE)").format(
                        id_other.percentatges_exempcio_splitted[2].replace('-', ''),
                        formatLang(id_other.percentatges_exempcio[0] * 100, digits=1)
                    )}
                %else:
                    ${_(u" (amb l'exempció del ")} ${id_other.excempcio})
                %endif
            </div>
            <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['tax_amount'])}</div>
        % else:
            <div class="detail_description_line">${_(u"Impost de l'electricitat")}</div>
            <div class="detail_description_line">${_(u"%s x 5,11269%%") % (formatLang(l['base_amount']))}</div>
            <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['tax_amount'])}</div>
        % endif
    </div>
    % endfor
    % for l in id_other.lloguer_lines:
    <div class="detail_line">
        <div class="detail_description_line">${_(u"Lloguer de comptador")}</div>
        <div class="detail_description_line">${_(u"%s dies x %s €/dia") % (int(l['quantity']), locale.str(locale.atof(formatLang(l['price_unit'], digits=6))))}</div>
        <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</div>
    </div>
    % endfor
    % for l in id_other.altres_lines:
    <div class="detail_line">
        <div class="detail_description_line">${l['name']}</div>
        <div class="detail_description_line">&nbsp;</div>
        <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</div>
    </div>
    % endfor
    % for l in id_other.iva_lines:
    <div class="detail_line">
        <div class="detail_description_line">${l['name']}</div>
        <div class="detail_description_line">${_(u"%s €") % (formatLang(l['base']))}${_(u"(BASE IMPOSABLE)")}</div>
        <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['amount'])}</div>
    </div>
    % endfor
    % for l in id_other.igic_lines:
    <div class="detail_line">
        <div class="detail_description_line">${l['name']}</div>
        <div class="detail_description_line">${_(u"%s €") % (formatLang(l['base']))}${_(u"(BASE IMPOSABLE)")}</div>
        <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['amount'])}</div>
    </div>
    % endfor
    % for l in id_other.donatiu_lines:
    <div style="float: left;width:89%;margin: 2em 10px 0px 10px;">
        <div class="detail_description_line">${_(u"Donatiu voluntari (exempt d'IVA)")}</div>
        <div class="detail_description_line">${_(u"%s kWh x %s €/kWh" % (formatLang(l['quantity']), formatLang(l['price_unit_multi'])))}</div>
        <div class="detail_description_subtotal">${_(u"%s €") % formatLang(l['price_subtotal'])}</div>
    </div>
    % endfor
    <p></p>
    <br />
    <div style="float: left; margin-top: 1em; width:100%;"><hr /></div>
    <div style="float: left;width:89%;margin: .5em 10px .5em 10px;">
        <div class="detail_description_line">${_(u"TOTAL IMPORT FACTURA")}</div>
        <div class="detail_description_line">&nbsp;</div>
        <div class="detail_description_subtotal">${_(u"%s &euro;") % formatLang(id_other.amount_total)}</div>
    </div>
    <br />
