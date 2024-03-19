<%page args="meter" />
<%import locale%>
% if False:
    ${_(u"Energia Activa (kWh)")}
    ${_(u'Energia Excedentària (kWh)')}
    ${_(u"Energia Reactiva Inductiva (kVArh)")}
    ${_(u"Energia Reactiva Capacitiva (kVArh)")}
    ${_(u"Maxímetre (kW)")}
    ${_(u"real")}
    ${_(u"calculada per Som Energia")}
    ${_(u"calculada")}
    ${_(u"estimada distribuïdora")}
% endif
% if meter.is_visible:
    <tr>
        <td class="td_first concepte_td" rowspan="3">${_(meter.title)}</td>
        <td class="detall_td">${_(u"Lectura inicial (%s) (%s)") % (meter.initial_date, _(meter.initial_type))}</td>
        % for p in meter.showing_periods:
            % if p in meter:
                <td>${_(u"%s") %(int(meter[p]["initial"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr>
        <td class="detall_td">${_(u"Lectura final (%s) (%s)") % (meter.final_date, _(meter.final_type))}</td>
        % for p in meter.showing_periods:
            % if p in meter:
                <td>${_(u"%s") %(int(meter[p]["final"]))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
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
                <td>${_(u"%s") %(int(round(meter[p]["total"])))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td>
        % if meter.adjust_reason != False:
            <sup>(2)</sup>
        % endif
        </td>
    </tr>
% endif
