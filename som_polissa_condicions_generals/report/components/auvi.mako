<%def name="auvi(polissa, prices, untaxed)">
    <tr>
        <td class="bold">${_(u"Terme energia (€/kWh)")}</td>
        <td class="center reset_line_height" colspan="6">
            <span class="normal_font_weight">
                <b>${_(u"Tarifa autoconsum virtual")}</b>${_(u"(2) - el preu horari (PH) es calcula d'acord amb la fórmula:")}
            </span>
            <br/>
            <!-- Pendent agafar el PAUVI des del ERP -->
            <span>${_(u"PHAUVI = 1,015 * [(PAUVI + Pc + Sc + Dsv + GdO + POsOm) (1 + Perd) + FE + F] + PTD + CA")}</span>

            %if polissa['tarifa'] != "2.0TD" and untaxed:
                <br/>
                <span class="normal_font_weight">${_(u"on la franja de la cooperativa")}</span>
                <span>&nbsp;${("(F) = %s €/kWh</B>") % formatLang(prices['coeficient_k_untaxed'], digits=6)}</span>
            %endif
            %if polissa['tarifa'] != "2.0TD" and not untaxed:
                <br/>
                <span class="normal_font_weight">${_(u"on la franja de la cooperativa")}</span>
                <span>&nbsp;${("(F) = %s €/kWh</B>") % formatLang(prices['coeficient_k'], digits=6)}</span>
            %endif

        </td>
    </tr>
    <tr>
        <td class="bold">${_(u"on PAUVI")}</td>
        <td class="center reset_line_height" colspan="6">
            <span class="">
                ${formatLang(prices['auvi_pauvi'], digits=6)}
            </span>
            <span class="">${_(u" €/MWh")}</span>
        </td>
    </tr>
    <tr>
        <td class="bold">${_(u"percentatge assignat")}</td>
        <td class="center reset_line_height" colspan="6">
            <span class="">
                ${("%s") % prices['auvi_name']} ${formatLang(prices['auvi_percent'], digits=2)} ${_(u"%")}
            </span>
        </td>
    </tr>
    %if polissa['tarifa'] == "2.0TD":
        <tr>
            <td class="bold">${_(u"on la franja de la cooperativa")}</td>
            <td class="center" colspan="3">
                <span class="">${("(F) = %s €/kWh</B>") % formatLang(prices['coeficient_k_untaxed'], digits=6)}</span>
            </td>
            <td class="center divisio_impostos" colspan="3">
                <span class="">${("(F) = %s €/kWh</B>") % formatLang(prices['coeficient_k'], digits=6)}</span>
            </td>
        </tr>
    %endif
</%def>
