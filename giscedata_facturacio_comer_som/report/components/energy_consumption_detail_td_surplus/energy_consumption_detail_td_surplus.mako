<%page args="meter" />
<%import locale%>
<%row_span = 2 if meter.hide_total_surplus else 3%>
% if meter.is_visible:
    <tr>
        <td class="td_first concepte_td" rowspan=${row_span}>${_(meter.title)}</td>
        <td class="detall_td">${_(u"Lectura inicial (%s) (%s)") % (meter.initial_date, _(meter.initial_type))}</td>
        % for p in meter.showing_periods:
            % if p in meter:
                <td class="periods_td">${_(u"%s") %(int(meter[p]["initial"]))}</td>
            % else:
                <td class="periods_td"></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr>
        % if meter.last_visible and meter.hide_total_surplus:
            <td class="detall_td">${_(u"Lectura final (%s) (%s)") % (meter.final_date, _(meter.final_type))}</td>
        % else:
            <td class="detall_td last_row">${_(u"Lectura final (%s) (%s)") % (meter.final_date, _(meter.final_type))}</td>
        % endif
        <td class="detall_td">${_(u"Lectura final (%s) (%s)") % (meter.final_date, _(meter.final_type))}</td>
        % for p in meter.showing_periods:
            % if p in meter:
                <td class="periods_td">${_(u"%s") %(int(meter[p]["final"]))}</td>
            % else:
                <td class="periods_td"></td>
            % endif
        % endfor
        <td></td>
    </tr>
    % if not meter.hide_total_surplus:
        % if meter.last_visible:
            <tr class="tr_bold">
        % else:
            <tr class="tr_bold last_row">
        % endif
            <td class="detall_td">${_(u"Total periode ")}
            % if meter.is_active:
                <sup class="sup_bold">(1)</sup>
            % endif
            </td>
            % for p in meter.showing_periods:
                % if p in meter:
                    <td class="periods_td">${_(u"%s") %(int(round(meter[p]["total"])))}</td>
                % else:
                    <td class="periods_td"></td>
                % endif
            % endfor
            <td class="periods_td">
            % if meter.adjust_reason != False:
                <sup>(2)</sup>
            % endif
            </td>
        </tr>
    % endif
% endif
