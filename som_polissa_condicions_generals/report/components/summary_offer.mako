<%def name="summary_offer(offer, prices, features, gurb)">
<%
    economic_summary = offer['economic_summary']
%>
<div class="summary-box">
    <h3>3. Resumen de la oferta y condiciones económicas</h3>
    <div class="summary-content">
        <p class="section-text"><span class="inline-label">Tarifa contratada:</span> ${offer['tariff_label']}</p>
        <p class="section-text"><span class="inline-label">Duración del contrato:</span> ${offer['duration_text']}</p>
        <p class="section-text inline-label">Potencias contratadas</p>
        <ul class="power-list">
            %for power in offer['powers']:
                <li>${power['period']}: ${power['power']} kW</li>
            %endfor
        </ul>

        %if economic_summary['validity_text']:
            <p class="section-text muted">${economic_summary['validity_text']}</p>
        %endif

        <p class="section-text inline-label">Resumen económico</p>
        <table class="summary-table">
            <tr>
                <th>Concepto</th>
                <th>Detalle</th>
            </tr>
            <tr>
                <td>Término potencia (€/kW y año)</td>
                <td>
                    %for index, power_price in enumerate(economic_summary['power_prices']):
                        ${power_price['period']}: ${formatLang(power_price['value'], digits=6)}%if index < len(economic_summary['power_prices']) - 1:, %endif
                    %endfor
                </td>
            </tr>
        %if economic_summary['is_indexed']:
            <tr>
                <td>Término energía (€/kWh)</td>
                <td>PH = 1,015 * [(PHM + Pc + Sc + Dsv + GdO + POsOm) (1 + Perd) + FE + F] + PTD + CA</td>
            </tr>
            <tr>
                <td>Franja de la cooperativa (F)</td>
                <td>${formatLang(economic_summary['cooperative_fee'], digits=6)} €/kWh</td>
            </tr>
        %else:
            <tr>
                <td>Término energía (€/kWh)</td>
                <td>
                    %for index, energy_price in enumerate(economic_summary['energy_prices']):
                        ${energy_price['period']}: ${formatLang(energy_price['value'], digits=6)}%if index < len(economic_summary['energy_prices']) - 1:, %endif
                    %endfor
                </td>
            </tr>
        %endif

        %if features['has_generation'] and economic_summary['generation_prices']:
            <tr>
                <td>Generation (€/kWh)</td>
                <td>
                    %for index, generation_price in enumerate(economic_summary['generation_prices']):
                        ${generation_price['period']}: ${formatLang(generation_price['value'], digits=6)}%if index < len(economic_summary['generation_prices']) - 1:, %endif
                    %endfor
                </td>
            </tr>
        %endif

        %if features['has_autoconsum'] and economic_summary['autoconsum_price'] not in (False, None):
            <tr>
                <td>Autoconsumo (€/kWh)</td>
                <td>${formatLang(economic_summary['autoconsum_price'], digits=6)}</td>
            </tr>
        %endif

        %if economic_summary['tax_text']:
            <tr>
                <td>Impuestos</td>
                <td>${economic_summary['tax_text']}</td>
            </tr>
        %endif
        </table>

        %if features['has_generation']:
            <p class="section-text">Generation: según condiciones del contrato Generation kWh.</p>
        %endif
        %if features['has_autoconsum']:
            <p class="section-text">Autoconsumo (€/kWh): precio de la compensación de excedentes, si es aplicable.</p>
        %endif
        %if features['has_gurb'] and gurb:
            <div class="spacer"></div>
            <p class="section-text inline-label">Servicio GURB</p>
            <p class="section-text">- Coste de adhesión: ${gurb.get('cost', '')}</p>
            <p class="section-text">- Potencia GURB (kW): ${gurb.get('potencia', '')}</p>
            <p class="section-text">- Quota GURB (€/kW/día): ${gurb.get('quota', '')}</p>
            <p class="section-text">- Beta contratada (%): ${gurb.get('beta_percentatge', '')}</p>
            <p class="section-text">- Beta contratada (kW): ${gurb.get('beta_kw', '')}</p>
        %endif
    </div>
</div>
</%def>
