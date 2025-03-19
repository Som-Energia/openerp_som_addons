<%page args="meters,location" />
% if location == meters.location:
    <style>
    <%include file="meters.css" />
    </style>
        %if meters.show_component:
            <div class="lectures_m${len(meters.periodes_a)>=3 and '30' or ''}">
                <table>
                    % for comptador in sorted(meters.lectures_real_a):
                        % if len(meters.lectures_real_a[comptador])>0:
                            <tr>
                                <th>&nbsp;</th>
                                % for periode in meters.periodes_a:
                                    <th style="text-align: center;">${periode}</th>
                                % endfor
                            </tr>
                            <tr>
                                <th>${_(u"Núm. de comptador")}</th>
                                % for p in meters.periodes_a:
                                    <td style="font-weight: normal;text-align: center;">${comptador}</td>
                                % endfor
                            </tr>
                            <tr>
                                <th>${_(u"Darrera lectura real ")}<span style="font-weight: 100">(${meters.lectures_real_a[comptador][0][2]})</span></th>
                                % for periode in meters.periodes_a:
                                    % if periode not in [lectura_real[0] for lectura_real in meters.lectures_real_a[comptador]]:
                                        <td></td>
                                    % else:
                                        <td style="text-align: center;">${int([lectura_real[1] for lectura_real in meters.lectures_real_a[comptador] if lectura_real[0] == periode][0])} KWh</td>
                                    % endif
                                % endfor
                            </tr>
                        %endif
                    % endfor
                </table>
            </div>
        %endif
% endif
