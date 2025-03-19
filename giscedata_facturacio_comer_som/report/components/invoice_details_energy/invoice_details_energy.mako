<%page args="id_energy" />
<style>
<%include file="invoice_details_energy.css" />
</style>
<% import locale %>
    <!-- ENERGIA -->
    <p><span style="font-weight: bold;">${_(u"Facturació per electricitat utilitzada")}</span> <br />
            ${_(u"Detall del càlcul del cost segons l'energia utilitzada:")} </p>

            % for l in id_energy.energy_lines:
                <div style="float: left;width:90%;margin: 0px 10px;">
                    <div style="border: 1px;font-weight: bold;float:left;width: 10%">
                        ${_(u"(%s)") % (l["name"],)}
                    </div>
                    <div style="border: 1px;font-weight: bold;float:left;width: 40%">
                        ${_(u"%s kWh x %s €/kWh") % (locale.str(locale.atof(formatLang(l["quantity"], digits=6))), locale.str(locale.atof(formatLang(l["price_unit_multi"], digits=6))))}
                    </div>
                    <div style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap; border: 1px;font-weight: bold;float:left;width: 30%">
                        ${l["gkwh_owner"]}
                    </div>
                    <div style="border: 1px;font-weight: bold; float:right;">
                        ${_(u"%s €") % formatLang(l["price_subtotal"])}
                    </div>
                </div><br />
            % endfor

            <p>
                ${_(u"D'aquest import, el cost per peatge d'accés ha estat de:")}
            </p>
            % for k, l in sorted(id_energy.atr_energy_lines.items()):
                <div style="float: left;width:90%;margin: 0px 10px;">
                    <div style="font-weight: bold;float:left">${_(u"(%s) %s kWh x %s €/kWh") % (k, locale.str(locale.atof(formatLang(l['quantity'], digits=6))), locale.str(locale.atof(formatLang(l['price'], digits=6))))}</div>
                    <div style="font-weight: bold; float:right;">${_(u"%s €") % formatLang(l['atrprice_subtotal'])}</div>
                </div><br />
            % endfor
    %if id_energy.is_new_tariff_message_visible:
        <p>
            ${_(u"Tal i com es va decidir a l’Assamblea del 2020, afegim el marge necessari al terme d'energia per a desenvolupar la nostra activitat de comercialització.")}
        </p>
    %else:
        <p>
          ${_(u"En el terme d'energia, afegim el marge necessari per a desenvolupar la nostra activitat de comercialització. Donem un major pes al terme variable de la factura, que depèn del nostre ús de l'energia. Busquem incentivar l'estalvi i l'eficiència energètica dels nostres socis/es i clients")}
        </p>
    %endif
