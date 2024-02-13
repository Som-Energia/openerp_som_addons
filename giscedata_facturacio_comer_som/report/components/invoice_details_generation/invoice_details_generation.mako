<%page args="id_generation" />
<style>
<%include file="invoice_details_generation.css" />
</style>
<% import locale %>
    % if id_generation.has_autoconsum:
        <!-- GENERACIO -->
        <p><span style="font-weight: bold;">${_(u"Compensació per electricitat autoproduïda")}</span> <br />
                ${_(u"Detall del càlcul de l'energia compensada:")} </p>

                % for l in id_generation.generation_lines:
                    % if l["is_visible"]:
                        <div style="float: left;width:90%;margin: 0px 10px;">
                            <div style="border: 1px;font-weight: bold;float:left;width: 10%">
                                ${_(u"(%s)") % (l["name"],)}
                            </div>
                            <div style="border: 1px;font-weight: bold;float:left;width: 40%">
                                ${_(u"%s kWh x %s €/kWh") % (locale.str(locale.atof(formatLang(l["quantity"], digits=6))), locale.str(locale.atof(formatLang(l["price_unit_multi"], digits=6))))}
                            </div>
                            <div style="border: 1px;font-weight: bold; float:right;">
                                ${_(u"%s €") % formatLang(l["price_subtotal"])}
                            </div>
                        </div><br />
                    % endif
                % endfor
        <p>
            ${_(u"Segons estableix el Reial Decret 244/2019 aquest import no serà mai superior a l'import per energia utilitzada. En cas que la compensació sigui superior a l'energia utilitzada, el terme d'energia serà igual a 0€")}
        </p>
        <hr/>
    % endif
