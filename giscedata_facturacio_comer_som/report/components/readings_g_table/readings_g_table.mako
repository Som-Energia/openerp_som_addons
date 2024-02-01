<%page args="readings" />
<style>
<%include file="readings_g_table.css" />
</style>
% if readings.is_visible:
    <div class="lectures_g${len(readings.periodes_g)>=3 and '30' or ''}">
        <table>
            <tr>
                <th>${_(u"Energia excedentària")}</th>
                % for periode in readings.periodes_g:
                    <th style="text-align: center;">${periode}</th>
                % endfor
            </tr>
            <%
                ajust_periode = []
            %>
            % for comptador in sorted(readings.lectures_g):
                <tr>
                    <th>${_(u"Núm. de comptador")}</th>
                    % for p in readings.periodes_g:
                        <td style="font-weight: normal;text-align: center;">${comptador}</td>
                    % endfor
                </tr>
                <tr>
                    <th>${_(u"Lectura anterior")}<span style="font-weight: 100">&nbsp;(${readings.lectures_g[comptador][0][4]})</span></th>
                    <!--%for lectura in lectures_g[comptador]:-->
                    % for periode in readings.periodes_g:
                        <%
                            for lectura in readings.lectures_g[comptador]:
                                if lectura[8] == 0:
                                    ajust_periode.append(False)
                                else:
                                    ajust_periode.append(True)
                        %>
                        % if periode not in [lectura[0] for lectura in readings.lectures_g[comptador]]:
                            <td></td>
                        % else:
                            <td style="text-align: center;">${int([lectura[1] for lectura in readings.lectures_g[comptador] if lectura[0] == periode][0])} kWh</td>
                        % endif
                    %endfor
                </tr>
                    <th>${_(u"Lectura final")}<span style="font-weight: 100">&nbsp;(${readings.lectures_g[comptador][0][5]})</span></th>
                    % for periode in readings.periodes_g:
                        % if periode not in [lectura[0] for lectura in readings.lectures_g[comptador]]:
                            <td></td>
                        % else:
                            <td style="text-align: center;">${int([lectura[2] for lectura in readings.lectures_g[comptador] if lectura[0] == periode][0])} kWh</td>
                        % endif
                    % endfor
                </tr>
            % endfor
            <tr>
                <th style="border-top: 1px solid #4c4c4c">${_(u"Total període")}</th>
                %for p in readings.periodes_g:
                    <td style="border-top: 1px solid #4c4c4c; text-align: center;">${formatLang(readings.total_lectures_g[p], digits=0)} kWh
                    % if ajust_periode[readings.periodes_g.index(p)]:
                        *
                    %endif
                    </td>
                %endfor
            </tr>
        </table>
    </div>
%endif
