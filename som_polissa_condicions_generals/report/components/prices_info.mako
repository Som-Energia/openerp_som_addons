<%def name="prices_info(polissa, prices)">
    <div class="styled_box">
    %for dades_tarifa in tarifes_a_mostrar:
        %if prices['text_vigencia']:
            <h5> ${_("TARIFES D'ELECTRICITAT")} ${text_vigencia}</h5>
        %else:
            <h5> ${_("TARIFES D'ELECTRICITAT")}</h5>
        %endif
        <div class="tarifes_electricitat">
            <table class="taula_custom new_taula_custom">
                <tr style="background-color: #878787;">
                    <th></th>
                    % if polissa['tarifa'] == "2.0TD":
                        <th>${_(u"Punta")}</th>
                        <th></th>
                        <th>${_(u"Vall")}</th>
                        <th></th>
                        <th></th>
                        <th></th>
                    % else:
                        <th>P1</th>
                        <th>P2</th>
                        <th>P3</th>
                        <th>P4</th>
                        <th>P5</th>
                        <th>P6</th>
                    % endif
                </tr>
                <tr>
                    <td class="bold">${_("Terme potència (€/kW i any)")}</td>
                    %if polissa['tarifa'] == "2.0TD":
                        %if polissa['pricelist']:
                            <td class="center">
                                <span>${formatLang(prices['power_prices'][polissa['periodes_potencia'][0]], digits=6)}</span>
                            </td>
                            <td></td>
                            <td class="center">
                                <span>${formatLang(prices['power_prices'][polissa['periodes_potencia'][1]], digits=6)}</span>
                            </td>
                            %for p in range(0, 3):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %else:
                            %for p in range(0, 6):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %endif
                    %else:
                        %for p in polissa['periodes_potencia']:
                            %if polissa['pricelist']:
                                <td class="center">
                                    <span><span>${formatLang(prices['power_prices'][p], digits=6)}</span></span>
                                </td>
                            %else:
                                %if lead:
                                    <td class="center">
                                        <span><span>${formatLang(prices['dict_preus_tp_potencia'][p], digits=6)}</span></span>
                                    </td>
                                %else:
                                    <td class="">
                                        &nbsp;
                                    </td>
                                %endif
                            %endif
                        %endfor
                        %if len(polissa['periodes_potencia']) < 6:
                            %for p in range(0, 6-len(polissa['periodes_potencia'])):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %endif
                    %endif
                </tr>

                % if polissa['tarifa'] == "2.0TD":
            </table>
            <table class="taula_custom doble_table new_taula_custom">
                <tr style="background-color: #878787;">
                        <th></th>
                        <th>${_(u"Punta")}</th>
                        <th>${_(u"Pla")}</th>
                        <th>${_(u"Vall")}</th>
                        <th></th>
                        <th></th>
                        <th></th>
                </tr>
                %endif
                <tr>
                    <td class="bold">${_("Terme energia (€/kWh)")}</td>
                    %if (polissa['mode_facturacio'] == 'index' and not polissa['modcon_pendent_periodes']) or polissa['modcon_pendent_indexada']:
                        <td class="center reset_line_height" colspan="6">
                            <span class="normal_font_weight">
                                <b>${_(u"Tarifa indexada")}</b>${_(u"(2) - el preu horari (PH) es calcula d'acord amb la fórmula:")}
                            </span>
                            <br/>
                            <span>${_(u"PH = 1,015 * [(PHM + Pc + Sc + Dsv + GdO + POsOm) (1 + Perd) + FE + F] + PTD + CA")}</span>
                            <br/>
                            <span class="normal_font_weight">${_(u"on la franja de la cooperativa")}</span>
                            <span>&nbsp;${("(F) = %s €/kWh</B>") % formatLang(pol['coeficient_k'], digits=6)}</span>
                        </td>
                    %else:
                        %for p in polissa['periodes_energia']:
                            %if polissa['pricelist'] and not polissa['lead']:
                                <% ctx['force_pricelist'] = polissa['pricelist'].id %>
                                <td class="center">
                                    <span class="">${formatLang(prices['power_prices'][p], digits=6)}</span>
                                </td>
                            %else:
                                %if lead:
                                    <td class="center">
                                        <span><span>${formatLang(preus['dict_preus_tp_energia'][p], digits=6)}</span></span>
                                    </td>
                                %else:
                                    <td class="">
                                        &nbsp;
                                    </td>
                                %endif
                            %endif
                        %endfor
                        %if len(polissa['periodes_energia']) < 6:
                            %for p in range(0, 6-len(polissa['periodes_energia'])):
                                <td class="">
                                    &nbsp;
                                </td>
                            %endfor
                        %endif
                    %endif
                </tr>
                %if polissa['te_assignacio_gkwh']:
                <tr>
                    <td class="bold">${_("(1) GenerationkWh (€/kWh)")}</td>
                    %for p in polissa['periodes_energia']:
                        %if polissa['pricelist']:
                            <td class="center">
                                <span class="">${formatLang(prices['generation_prices'][p], digits=6)}</span>
                            </td>
                        %else:
                            <td class="">
                                &nbsp;
                            </td>
                        %endif
                    %endfor
                    %if len(polissa['periodes_energia']) < 6:
                        %for p in range(0, 6-len(polissa['periodes_energia'])):
                            <td class="">
                                &nbsp;
                            </td>
                        %endfor
                    %endif
                </tr>
                %endif
                %if polissa['auto'] != '00':
                <tr>
                    <td><span class="bold auto">${_("Excedents d'autoconsum (€/kWh)")}</span></td>
                    %if (polissa['mode_facturacio'] == 'index' and not polissa['modcon_pendent_periodes']) or polissa['modcon_pendent_indexada']:
                        <td class="center reset_line_height" colspan="6">
                            <span class="normal_font_weight">${_(u"Tarifa indexada(2) - el preu horari de la compensació d'excedents és igual al PHM")}</span>
                        </td>
                    %else:
                        %if polissa['pricelist']:
                            <td colspan="6">
                                <hr class="hr-text" data-content="${formatLang(prices['price_auto'], digits=6)}"/>
                            </td>
                        %else:
                            <td colspan="6">
                                &nbsp;
                            </td>
                        %endif
                    %endif
                </tr>
                %endif
            </table>
            <div class="padding_top padding_left padding_right">
            %if polissa['te_assignacio_gkwh']:
                <span class="bold">(1) </span> ${_("Terme d'energia en cas de participar-hi, segons condicions del contracte GenerationkWh.")}<br/>
            %endif
            %if (polissa['mode_facturacio'] == 'index' and not polissa['modcon_pendent_periodes']) or polissa['modcon_pendent_indexada']:
                <span class="bold">(2) </span> ${_("Pots consultar el significat de les variables a les condicions específiques que trobaràs a continuació.")}
            %endif
            </div>
        </div>
        <%
            if lead:
                break
        %>
        %endfor
    </div>
</%def>