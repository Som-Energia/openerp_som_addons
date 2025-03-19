<%page args="readings_r" />
<style>
<%include file="reactive_readings_table_td.css" />
</style>
% if readings_r.is_visible:
    <div class="lectures_reactiva${len(readings_r.periodes_r)>=3 and '30' or ''}">
        <h1>${_(u"ENERGIA REACTIVA")}</h1>
        <table style="margin: 1em">
            % for comptador in sorted(readings_r.lectures_r):
                <% comptador = sorted(readings_r.lectures_r)[0] %>
                <tr>
                    <th>&nbsp;</th>
                    % for periode in readings_r.periodes_r:
                        <th style="text-align: center;">${periode}</th>
                    % endfor
                </tr>
                <tr>
                    <th>${_(u"Núm. de comptador")}</th>
                    % for p in readings_r.periodes_r:
                        <td style="font-weight: normal;text-align: center;">${comptador}</td>
                    % endfor
                </tr>
                <tr>
                    <th>${_(u"Lectura anterior")}<span style="font-weight: 100">&nbsp;(${readings_r.lectures_r[comptador][0][4]}) (${readings_r.lectures_r[comptador][0][6]})</span></th>
                    % for periode in readings_r.periodes_r:
                        % if periode not in [lectura_real[0] for lectura_real in readings_r.lectures_r[comptador]]:
                            <td></td>
                        % else:
                            <td style="text-align: center;">${int([lectura[1] for lectura in readings_r.lectures_r[comptador] if lectura[0] == periode][0])} kVArh</td>
                        % endif
                    % endfor
                </tr>
                <tr>
                    <th>${_(u"Lectura final")}<span style="font-weight: 100">&nbsp;(${readings_r.lectures_r[comptador][0][5]}) (${readings_r.lectures_r[comptador][0][7]})</span></th>
                    % for periode in readings_r.periodes_r:
                        % if periode not in [lectura_real[0] for lectura_real in readings_r.lectures_r[comptador]]:
                            <td></td>
                        % else:
                            <td style="text-align: center;">${int([lectura[2] for lectura in readings_r.lectures_r[comptador] if lectura[0] == periode][0])} kVArh</td>
                        % endif
                    % endfor
                </tr>
                <tr>
                    <th>${_(u"Total període")}</th>
                    % for periode in readings_r.periodes_r:
                        <td style="text-align: center;">${formatLang(readings_r.total_lectures_r[periode], digits=0)} kVArh</td>
                    % endfor
                </tr>
            %endfor

        </table>
        %if any([readings_r.lectures_r[comptador][0][7] != "real" for comptador in sorted(readings_r.lectures_r) if len(readings_r.lectures_real_r[comptador])>0]):
            <table style="margin: 1em">
                % for comptador in sorted(readings_r.lectures_real_r):
                    % if len(readings_r.lectures_real_r[comptador])>0:
                        <tr>
                            <th>&nbsp;</th>
                            % for periode in readings_r.periodes_r:
                                <th style="text-align: center;">${periode}</th>
                            % endfor
                        </tr>
                        <tr>
                            <th>${_(u"Núm. de comptador")}</th>
                            % for p in readings_r.periodes_r:
                                <td style="font-weight: normal;text-align: center;">${comptador}</td>
                            % endfor
                        </tr>
                        <tr>
                            <th>${_(u"Darrera lectura real ")}<span style="font-weight: 100">(${readings_r.lectures_real_r[comptador][0][2]})</span></th>
                            % for periode in readings_r.periodes_r:
                                % if periode not in [lectura_real[0] for lectura_real in readings_r.lectures_real_r[comptador]]:
                                    <td></td>
                                % else:
                                    <td style="text-align: center;">${int([lectura_real[1] for lectura_real in readings_r.lectures_real_r[comptador] if lectura_real[0] == periode][0])} KVArh</td>
                                % endif
                            % endfor
                        </tr>
                    % endif
                %endfor
            </table>
        %endif
    </div>
% endif
