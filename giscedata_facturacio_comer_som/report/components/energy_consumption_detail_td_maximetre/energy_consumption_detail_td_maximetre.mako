<%page args="meter" />
<%import locale%>

% if meter.is_visible:
    % if len(meter.showing_periods) == 3:
        <tr>
            <td class="td_first concepte_td" rowspan="3">${_(u"Maxímetre (kW)")}</td>

            <td class="detall_td">${_(u"Potència contractada")}</td>
            % for p in meter.showing_periods[:-1]:
                % if p in meter:
                    % if p == 'P1':
                        <td colspan="2">${_(u"%s") %(formatLang(meter[p]["contracted"], digits=3))}</td>
                    % else:
                        <td>${_(u"%s") %(formatLang(meter[p]["contracted"], digits=3))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
            <td></td>
        </tr>
        <tr>
            <td class="detall_td">${_(u"Potència maxímetre")}</td>
            % for p in meter.showing_periods[:-1]:
                % if p in meter:
                    % if p == 'P1':
                        <td colspan="2">${_(u"%s") %(formatLang(meter[p]["reading"], digits=3))}</td>
                    % else:
                        <td>${_(u"%s") %(formatLang(meter[p]["reading"], digits=3))}</td>
                    % endif
                % else:
                    <td></td>
                % endif
            % endfor
            <td></td>
        </tr>
        % if meter.is_visible_surplus:
            <tr>
                <td class="detall_td">${_(u"Potència excedida")}</td>
                % for p in meter.showing_periods:
                    % if p in meter:
                        % if p == 'P1':
                            <td colspan="2">${_(u"%s") %(formatLang(meter[p]["surplus"], digits=3))}</td>
                        % else:
                            <td>${_(u"%s") %(formatLang(meter[p]["surplus"], digits=3))}</td>
                        % endif
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
            </tr>
        % endif
    % else:
        <tr>
            <td class="td_first concepte_td" rowspan="3">${_(u"Maximetre (kW)")}</td>

            <td class="detall_td">${_(u"Potència contractada")}</td>
            % for p in meter.showing_periods:
                % if p in meter:
                    <td>${_(u"%s") %(formatLang(meter[p]["contracted"], digits=3))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
            <td></td>
        </tr>
        <tr>
            <td class="detall_td">${_(u"Potència maxímetre")}</td>
            % for p in meter.showing_periods:
                % if p in meter:
                    <td>${_(u"%s") %(formatLang(meter[p]["reading"], digits=3))}</td>
                % else:
                    <td></td>
                % endif
            % endfor
            <td></td>
        </tr>
        % if meter.is_visible_surplus:
            <tr>
                <td class="detall_td">${_(u"Potència excedida")}</td>
                % for p in meter.showing_periods:
                    % if p in meter:
                        <td>${_(u"%s") %(formatLang(meter[p]["surplus"], digits=3))}</td>
                    % else:
                        <td></td>
                    % endif
                % endfor
                <td></td>
            </tr>
        % endif
    % endif
% endif
