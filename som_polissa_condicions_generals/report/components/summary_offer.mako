<%def name="summary_offer(offer, features, gurb)">
<div class="summary-box">
    <h3>${_(u"3. Resum de l'oferta i condicions econòmiques")}</h3>
    <div class="summary-content">
        <p class="section-text"><span class="inline-label">${_(u"Tarifa contractada:")}</span> ${offer['tariff_label']}</p>
        <p class="section-text"><span class="inline-label">${_(u"Durada del contracte:")}</span>
            %if offer['duration_quarter'] == 1:
                ${_(u"1r trimestre {}").format(offer['duration_year'])}
            %elif offer['duration_quarter'] == 2:
                ${_(u"2n trimestre {}").format(offer['duration_year'])}
            %elif offer['duration_quarter'] == 3:
                ${_(u"3r trimestre {}").format(offer['duration_year'])}
            %else:
                ${_(u"4t trimestre {}").format(offer['duration_year'])}
            %endif
        </p>
        <p class="section-text inline-label">${_(u"Potències contractades")}</p>
        <ul class="power-list">
            %for power in offer['powers']:
                <li>${power['period']}: ${power['power']} kW</li>
            %endfor
        </ul>

        %for price_summary in offer['price_summaries']:
        <%
            economic_summary = price_summary['economic_summary']
        %>
        %if price_summary['validity_text']:
            <p class="section-text muted">${price_summary['validity_text']}</p>
        %endif

        <p class="section-text inline-label">${_(u"Resum econòmic")}</p>
        <table class="summary-table">
            <tr>
                <th>${_(u"Concepte")}</th>
                <th>${_(u"Detall")}</th>
            </tr>
            <tr>
                <td>${_(u"Terme potència (€/kW i any)")}</td>
                <td>
                    ${", ".join([
                        "%s: %s" % (
                            power_price['period'],
                            formatLang(power_price['value'], digits=6)
                        )
                        for power_price in economic_summary['power_prices']
                    ])}
                </td>
            </tr>
        %if offer['is_indexed']:
            <tr>
                <td>${_(u"Terme energia (€/kWh)")}</td>
                <td>PH = 1,015 * [(PHM + Pc + Sc + Dsv + GdO + POsOm) (1 + Perd) + FE + F] + PTD + CA</td>
            </tr>
            <tr>
                <td>${_(u"Franja de la cooperativa (F)")}</td>
                <td>${formatLang(economic_summary['cooperative_fee'], digits=6)} €/kWh</td>
            </tr>
        %else:
            <tr>
                <td>${_(u"Terme energia (€/kWh)")}</td>
                <td>
                    ${", ".join([
                        "%s: %s" % (
                            energy_price['period'],
                            formatLang(energy_price['value'], digits=6)
                        )
                        for energy_price in economic_summary['energy_prices']
                    ])}
                </td>
            </tr>
        %endif

        %if features['has_generation'] and economic_summary['generation_prices']:
            <tr>
                <td>Generation (€/kWh)</td>
                <td>
                    ${", ".join([
                        "%s: %s" % (
                            generation_price['period'],
                            formatLang(generation_price['value'], digits=6)
                        )
                        for generation_price in economic_summary['generation_prices']
                    ])}
                </td>
            </tr>
        %endif

        %if features['has_autoconsum'] and economic_summary['autoconsum_price'] not in (False, None):
            <tr>
                <td>${_(u"Autoconsum (€/kWh)")}</td>
                <td>${formatLang(economic_summary['autoconsum_price'], digits=6)}</td>
            </tr>
        %endif

        %if economic_summary['tax_text']:
            <tr>
                <td>${_(u"Impostos")}</td>
                <td>${economic_summary['tax_text']}</td>
            </tr>
        %endif
        </table>
        %endfor

        %if features['has_generation']:
            <p class="section-text">${_(u"Generation: segons condicions del contracte Generation kWh.")}</p>
        %endif
        %if features['has_autoconsum']:
            <p class="section-text">${_(u"Autoconsum (€/kWh): preu de la compensació d'excedents, si és aplicable.")}</p>
        %endif
        %if features['has_gurb'] and gurb:
            <div class="spacer"></div>
            <p class="section-text inline-label">${_(u"Servei GURB")}</p>
            <p class="section-text">- ${_(u"Cost d'adhesió:")} ${gurb.get('cost', '')}</p>
            <p class="section-text">- ${_(u"Potència GURB (kW):")} ${gurb.get('potencia', '')}</p>
            <p class="section-text">- ${_(u"Quota GURB (€/kW/dia):")} ${gurb.get('quota', '')}</p>
            <p class="section-text">- ${_(u"Beta contractada (%):")} ${gurb.get('beta_percentatge', '')}</p>
            <p class="section-text">- ${_(u"Beta contractada (kW):")} ${gurb.get('beta_kw', '')}</p>
        %endif
    </div>
</div>
</%def>
