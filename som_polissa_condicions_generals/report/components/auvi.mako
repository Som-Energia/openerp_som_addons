<%def name="auvi(polissa, prices)">
    <tr>
        <td class="bold">${_(u"Terme energia (€/kWh)")}</td>
        <td class="center reset_line_height" colspan="6">
            <span class="normal_font_weight">
                <b>${_(u"Tarifa autoconsum virtual")}</b>${_(u"(2) - el preu horari (PH) es calcula d'acord amb la fórmula:")}
            </span>
            <br/>
            <!-- Pendent agafar el PAUVI des del ERP -->
            <span>${_(u"PHAUVI = 1,015 * [(PAUVI + Pc + Sc + Dsv + GdO + POsOm) (1 + Perd) + FE + F] + PTD + CA")}</span>
            <br/>
            <b>${_(u"Percentatge i assignat")}</b> <!-- Percentatge AUVI -->
        </td>
    </tr>
</%def>
