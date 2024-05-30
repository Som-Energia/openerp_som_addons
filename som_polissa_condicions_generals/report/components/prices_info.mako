<%def name="prices_info(polissa, prices)">
    <%
        ## ctx = {'date': datetime.today()}
        ## if polissa.data_baixa:
        ##     ctx = {'date': datetime.strptime(polissa.data_baixa, '%Y-%m-%d')}
        ## if not polissa.llista_preu:
        ##     tarifes_a_mostrar = []
        ##     if lead and dict_preus_tp_potencia:
        ##         tarifes_a_mostrar = [dict_preus_tp_potencia]
        ## else:
        ##     tarifes_a_mostrar = get_comming_atr_price(cursor, uid, polissa, ctx)
        ## text_vigencia = ''

        #unused
        ## cfg_obj = polissa.pool.get('res.config')
        ## start_date_mecanisme_ajust_gas = cfg_obj.get(
        ## cursor, uid, 'start_date_mecanisme_ajust_gas', '2022-10-01'
        ## )
        ## end_date_mecanisme_ajust_gas = cfg_obj.get(
        ##     cursor, uid, 'end_date_mecanisme_ajust_gas', '2023-12-31'
        ## )

        #migrated
        ## start_date_iva_10 = cfg_obj.get(
        ##     cursor, uid, 'charge_iva_10_percent_when_start_date', '2021-06-01'
        ## )
        ## end_date_iva_10 = cfg_obj.get(
        ##     cursor, uid, 'iva_reduit_get_tariff_prices_end_date', '2024-12-31'
        ## )
        ## iva_10_active = eval(cfg_obj.get(
        ##     cursor, uid, 'charge_iva_10_percent_when_available', '0'
        ## ))
        ## omie_obj = polissa.pool.get('giscedata.monthly.price.omie')

    %>
    <div class="styled_box">
    %for dades_tarifa in tarifes_a_mostrar:
    ##     <%
    ##         if modcon_pendent_indexada or modcon_pendent_periodes or lead:
    ##             text_vigencia = ''
    ##         elif not data_final and dades_tarifa['date_end']:
    ##             text_vigencia = _(u"(vigents fins al {})").format(dades_tarifa['date_end'])
    ##         elif dades_tarifa['date_end'] and dades_tarifa['date_start']:
    ##             text_vigencia = _(u"(vigents fins al {})").format((datetime.strptime(dades_tarifa['date_end'], '%Y-%m-%d')).strftime('%d/%m/%Y'))
    ##         elif datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d') > datetime.today():
    ##             text_vigencia = _(u"(vigents a partir del {})").format(datetime.strptime(dades_tarifa['date_start'], '%Y-%m-%d').strftime('%d/%m/%Y'))
    ## try:
    ##     omie_mon_price_45 = omie_obj.has_to_charge_10_percent_requeriments_oficials(cursor, uid, ctx['date'], polissa.potencia)
    ## except:
    ##     omie_mon_price_45 = False

    ##         iva_reduit = False
    ##         if not polissa.fiscal_position_id and not lead:
    ##             imd_obj = polissa.pool.get('ir.model.data')
    ##             if iva_10_active and polissa.potencia <= 10 and dades_tarifa['date_start'] >= start_date_iva_10 and dades_tarifa['date_start'] <= end_date_iva_10 and omie_mon_price_45:
    ##                 fp_id = imd_obj.get_object_reference(cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
    ##                 iva_reduit = True
    ##                 text_vigencia += " (IVA 10%, IE 3,8%)"
    ##             else:
    ##                 fp_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_iese', 'fp_nacional_2024_rdl_8_2023_38')[1]
    ##                 text_vigencia += " (IVA 21%, IE 3,8%)"
    ##             ctx.update({'force_fiscal_position': fp_id})
    ##     %>
        %if prices['text_vigencia']:
            <h5> ${_("TARIFES D'ELECTRICITAT")} ${text_vigencia}</h5>
        %else:
            <h5> ${_("TARIFES D'ELECTRICITAT")}</h5>
        %endif
        <%
            ## if potencies:
            ##     if potencies['periodes'] and not lead:
            ##         if data_final: #TODO: A LA SEGONA PASSADA, POSARIEM ELS PREUS VELLS
            ##             data_llista_preus = dades_tarifa['date_start']
            ##             if datetime.strptime(data_llista_preus, '%Y-%m-%d') <= datetime.today():
            ##                 data_llista_preus = min(datetime.strptime(data_final, '%Y-%m-%d'), datetime.today())
            ##             ctx['date'] = data_llista_preus
            ##         if not lead:
            ##             data_i = data_inici and datetime.strptime(polissa.modcontractual_activa.data_inici, '%Y-%m-%d')
            ##         else:
            ##             data_i = datetime.strptime(data_inici, '%Y-%m-%d')
            ##         if data_i and calendar.isleap(data_i.year):
            ##             dies = 366
            ##         else:
            ##             dies = 365
        %>
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
                                <span>${formatLang(get_atr_price(cursor, uid, polissa, polissa['periodes_potencia'][0], 'tp', ctx, with_taxes=True)[0], digits=6)}</span>
                            </td>
                            <td></td>
                            <td class="center">
                                <span>${formatLang(get_atr_price(cursor, uid, polissa, polissa['periodes_potencia'][1], 'tp', ctx, with_taxes=True)[0], digits=6)}</span>
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
                                    <span><span>${formatLang(get_atr_price(cursor, uid, polissa, p, 'tp', ctx, with_taxes=True)[0], digits=6)}</span></span>
                                </td>
                            %else:
                                %if lead:
                                    <td class="center">
                                        <span><span>${formatLang(dict_preus_tp_potencia[p], digits=6)}</span></span>
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
                            <span>${_(u"PH = 1,015 * [(PHM + PHMA + Pc + Sc + I + POsOm) (1 + Perd) + FE + F] + PTD + CA")}</span>
                            <br/>
                            <span class="normal_font_weight">${_(u"on la franja de la cooperativa")}</span>
                            <%
                                ## coeficient_k = (polissa.coeficient_k + polissa.coeficient_d)/1000
                                ## if coeficient_k == 0:
                                ##     today = datetime.today().strftime("%Y-%m-%d")
                                ##     vlp = None
                                ##     if modcon_pendent_indexada:
                                ##         llista_preus = ultima_modcon.llista_preu.version_id
                                ##     else:
                                ##         llista_preus = polissa.llista_preu.version_id
                                ##     for lp in llista_preus:
                                ##         if lp.date_start <= today and (not lp.date_end or lp.date_end >= today):
                                ##             vlp = lp
                                ##             break
                                ##     if vlp:
                                ##         for item in vlp.items_id:
                                ##             if item.name == 'Coeficient K':
                                ##                 coeficient_k = item.base_price
                                ##                 break
                            %>
                            <span>&nbsp;${("(F) = %s €/kWh</B>") % formatLang(pol['coeficient_k'], digits=6)}</span>
                        </td>
                    %else:
                        ## <% llista_preu = ultima_modcon.llista_preu if modcon_pendent_periodes else polissa.llista_preu %>
                        %for p in polissa['periodes_energia']:
                            %if polissa['pricelist'] and not polissa['lead']:
                                <% ctx['force_pricelist'] = polissa['pricelist'].id %>
                                <td class="center">
                                    <span class="">${formatLang(get_atr_price(cursor, uid, polissa, p, 'te', ctx, with_taxes=True)[0], digits=6)}</span>
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
                                <span class="">${formatLang(get_gkwh_atr_price(cursor, uid, polissa, p, ctx, with_taxes=True)[0], digits=6)}</span>
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
                                <hr class="hr-text" data-content="${formatLang(get_atr_price(cursor, uid, polissa, polissa['periodes_energia'][0], 'ac', ctx, with_taxes=True)[0], digits=6)}"/>
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