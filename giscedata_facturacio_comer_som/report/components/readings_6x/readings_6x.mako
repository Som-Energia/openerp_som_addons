<%page args="readings_6x" />
<style>
<%include file="readings_6x.css" />
</style>
    <%
        # code below seems that has not sense, copied from original mako. minor fixes applied.
        ajust_fet = True
        motiu_ajust = ''
    %>
    <div class="lectures_6x">
        %for key in readings_6x.comptadors.keys():
            <table style="border: 1px #c1c1c1 solid;">
                <tr>
                    <td>&nbsp;</td>
                    <th class="center">${_("Lectura anterior")}<br/> ${readings_6x.comptadors[key][0][3]}
                    <br/>${key[2]}</th>
                    <th class="center">${_("Lectura actual")}<br/> ${readings_6x.comptadors[key][0][3]}
                    <br/>${key[1]}</th>
                    <th class="center">${_("Consum")} <br/> ${_("en el període")}</th>
                </tr>
                <%
                    period_counter = 1
                %>
                %for lectures in readings_6x.comptadors[key]:
                    <!-- Recorremos las lecturas del contador actual -->
                    <%
                        comptador = 0
                    %>
                    <tr>
                        <th class="center">P${period_counter}</th>
                        %for lectura in lectures:
                            <!--
                                Recorremos cada lectura individual. El contador (comptador) es utilizado
                                para conocer cual de los 3 elementos estamos recorriendo (activa, reactiva o maxímetro).
                            -->
                                %if comptador in (0, 1) and lectura:
                                    %if comptador == 0:
                                        %if period_counter == 4:
                                            <td class="center">${formatLang(int(lectura.lect_anterior), 0)} kWh</td>
                                            <td class="center">${formatLang(int(lectura.lect_actual), 0)} kWh
                                        %else:
                                            <td class="center">${formatLang(int(lectura.lect_anterior), 0)} kWh</td>
                                            <td class="center">${formatLang(int(lectura.lect_actual), 0)} kWh
                                        %endif
                                    %endif
                                    %if lectura.ajust and not ajust_fet:
                                        ${str(lectura.ajust) + "*"}
                                    %endif
                                    <%
                                    if lectura.motiu_ajust and not motiu_ajust == '':
                                        ajust_fet = True
                                        motiu_ajust = lectura.motiu_ajust
                                    %>
                                    </td>
                                    %if comptador == 0:
                                        %if period_counter == 4:
                                            <td class="center">${formatLang(int(lectura.consum), 0)} kWh</td>
                                        %else:
                                            <td class="center">${formatLang(int(lectura.consum), 0)} kWh</td>
                                        %endif
                                    %endif
                                %endif
                            <%
                                comptador += 1
                            %>
                        %endfor
                    </tr>
                    <%
                        period_counter += 1
                    %>
                %endfor
            </table>
        %endfor
        <div style="text-align: center"><p>${_(u"La despesa diària és de %s € que correspon a %s kWh/dia (%s dies).") % (formatLang(readings_6x.diari_factura_actual_eur), formatLang(readings_6x.diari_factura_actual_kwh), readings_6x.dies_factura or 1)}</p></div>
    </div>
