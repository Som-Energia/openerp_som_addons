<%page args="readings" />
<style>
<%include file="readings_table.css" />
</style>
    <div class="lectures${len(readings.periodes_a)>=3 and '30' or ''}">
        <table>
            <tr>
                %if readings.has_autoconsum:
                    <th>${_(u"Energia utilitzada")}</th>
                %else:
                    <th>&nbsp;</th>
                %endif
                % for periode in readings.periodes_a:
                    <th style="text-align: center;">${periode}</th>
                % endfor
            </tr>
            <%
                ajust_periode = []
            %>
            % for comptador in sorted(readings.lectures_a):
                <tr>
                    <th>${_(u"Núm. de comptador")}</th>
                    % for p in readings.periodes_a:
                        <td style="font-weight: normal;text-align: center;">${comptador}</td>
                    % endfor
                </tr>
                <tr>
                    <th>${_(u"Lectura anterior")}<span style="font-weight: 100">&nbsp;(${readings.lectures_a[comptador][0][4]})&nbsp;(${readings.lectures_a[comptador][0][6]})</span></th>
                    <!--%for lectura in lectures_a[comptador]:-->
                    % for periode in readings.periodes_a:
                        <%
                            for lectura in readings.lectures_a[comptador]:
                                if lectura[8] == 0:
                                    ajust_periode.append(False)
                                else:
                                    ajust_periode.append(True)
                        %>
                        % if periode not in [lectura[0] for lectura in readings.lectures_a[comptador]]:
                            <td></td>
                        % else:
                            <td style="text-align: center;">${int([lectura[1] for lectura in readings.lectures_a[comptador] if lectura[0] == periode][0])} kWh</td>
                        % endif
                    %endfor
                </tr>
                    <th>${_(u"Lectura final")}<span style="font-weight: 100">&nbsp;(${readings.lectures_a[comptador][0][5]})&nbsp;(${readings.lectures_a[comptador][0][7]})</span></th>
                    % for periode in readings.periodes_a:
                        % if periode not in [lectura[0] for lectura in readings.lectures_a[comptador]]:
                            <td></td>
                        % else:
                            <td style="text-align: center;">${int([lectura[2] for lectura in readings.lectures_a[comptador] if lectura[0] == periode][0])} kWh</td>
                        % endif
                    % endfor
                </tr>
            % endfor
            <tr>
                <th style="border-top: 1px solid #4c4c4c">${_(u"Total període")}</th>
                %for p in readings.periodes_a:
                    <td style="border-top: 1px solid #4c4c4c; text-align: center;">${formatLang(readings.total_lectures_a[p], digits=0)} kWh
                    % if ajust_periode[readings.periodes_a.index(p)]:
                        *
                    %endif
                    </td>
                %endfor
            </tr>
        </table>
        <div class="despesa_diaria"><p>${_(u"La despesa diària és de %s € que correspon a %s kWh/dia (%s dies).") % (formatLang(readings.diari_factura_actual_eur), formatLang(readings.diari_factura_actual_kwh), readings.dies_factura or 1)}</p></div>
    </div>
