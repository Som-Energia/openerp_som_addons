<%page args="id_reactive" />
<style>
<%include file="invoice_details_reactive.css" />
</style>
<% import locale %>
    % if id_reactive.is_visible:
        <!-- REACTIVA -->
        <p><span style="font-weight: bold;">${_(u"Facturació per penalització de reactiva")}</span> <br />
            ${_(u"Detall del càlcul del cost segons la penalització per reactiva:")} <br /></p>
        % for l in id_reactive.reactive_lines:
         <div style="float: left;width:90%;margin: 0px 10px;">
             <div style="font-weight: bold;float:left">${_(u"(%s) %s kVArh x %s €/kVArh") % (l["name"], formatLang(l["quantity"]), locale.str(locale.atof(formatLang(l["price_unit_multi"], digits=6))))}</div>
             <div style="font-weight: bold; float:right">${_(u"%s €") % formatLang(l["price_subtotal"])}</div>
         </div><br />
        % endfor
        <p>${_(u"Detall del cost per peatge de penalització de reactiva inclós en l'import resultant:")}
        </p>
        % for l in id_reactive.reactive_lines:
         <div style="float: left;width:90%;margin: 0px 10px;">
             <div style="font-weight: bold;float:left">${_(u"(%s) %s kVArh x %s €/kVArh") % (l["name"], formatLang(l["quantity"]), locale.str(locale.atof(formatLang(l["atr_price"], digits=6))))}</div>
             <div style="font-weight: bold; float:right;">${_(u"%s €") % formatLang(l["atrprice_subtotal"])}</div>
         </div><br />
        % endfor
        <br />
        <hr />
    % endif
