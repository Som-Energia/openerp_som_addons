<%page args="id_power" />
<style>
<%include file="invoice_details_power.css" />
</style>
<% import locale %>
    <!-- POTÈNCIA -->
    <p><span style="font-weight: bold;">${_(u"Facturació per potència contractada")}</span> <br />
    ${_(u"Detall del càlcul del cost segons potència contractada:")} <br /></p>
    % for l in id_power.power_lines:
        <div style="float: left;width:90%;margin: 0px 10px;">
        <div style="font-weight: bold;float:left">${_(u"(%s) %s kW x %s €/kW i any x (%.f/%d) dies") % (l["name"], locale.str(locale.atof(formatLang(l["quantity"], digits=3))), locale.str(locale.atof(formatLang(l["atr_price"], digits=6))),int(l["multi"]), l["days_per_year"])}</div>
        <div style="font-weight: bold; float:right;">${_(u"%s €") % formatLang(l["price_subtotal"])}</div>
        </div><br />
    % endfor
    % if id_power.is_6X:
        <br/>
        <div style="float: left;width:90%;margin: 0px 10px;">
            <div style="font-weight: bold;float:left">
                ${_(u"Import Excés de Potència")}
            </div>
            <div style="font-weight: bold; float:right;">${"%s &euro;" % formatLang(id_power.total_exces_consumida)}</div>
        </div>
        <br/>
    %endif
    % if id_power.is_power_tolls_visible:
        <p>
            ${_(u"D'aquest import, el cost per peatge d'accés ha estat de:")}
        </p>
        % for k, l in sorted(id_power.atr_power_lines.items()):
            <div style="float: left;width:90%;margin: 0px 10px;">
                <div style="font-weight: bold;float:left">${_(u"(%s) %s kW x %s €/kW i any x (%.f/%d) dies") % (k, locale.str(locale.atof(formatLang(l['quantity'], digits=6))), locale.str(locale.atof(formatLang(l['price'], digits=6))),int(l["multi"]), l["days_per_year"])}</div>
                <div style="font-weight: bold; float:right;">${_(u"%s €") % formatLang(l['atrprice_subtotal'])}</div>
            </div><br />
        % endfor
        <p style="display:block;clear:both;">
            ${_(u"Tal i com es va decidir a l’Assamblea del 2020, afegim el marge necessari al terme de potència per a desenvolupar la nostra activitat de comercialització.")}
        </p>
    %else:
        </br>
    %endif
