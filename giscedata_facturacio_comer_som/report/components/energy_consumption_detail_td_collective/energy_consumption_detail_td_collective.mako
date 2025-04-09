<%page args="coll" />
<%import locale%>
% if False:
    ${}
% endif
% if coll.is_visible:
    <tr>
        <td class="td_first concepte_td" rowspan="3">${_(u"Autoconsum compartit (kWh)")}</td>
        <td class="detall_td">${_(u"Generació segons coeficient de repartiment (periode del %s fins al %s)") % (coll.initial_date, coll.final_date)}</td>
        % for p in coll.showing_periods:
            % if p in coll:
                % data = coll[p].get("generacio_neta", 0.0)
                <td>${_(u"%s") %(formatLang(data, digits=3))}</td>
                ## <td>${_(u"%s") %(formatLang(coll[p]["generacio_neta"], digits=3))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    <tr>
        <td class="detall_td">${_(u"Energia autoconsumida (periode del %s fins al %s)") % (coll.initial_date, coll.final_date)}</td>
        % for p in coll.showing_periods:
            % if p in coll:
                % data = coll[p].get("autoconsum", 0.0)
                <td>${_(u"%s") %(formatLang(data, digits=3))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td></td>
    </tr>
    % if coll.last_visible:
        <tr class="tr_bold">
    % else:
        <tr class="tr_bold last_row">
    % endif
        <td class="detall_td">${_(u"Excedent")}
        % if coll.is_active:
            <sup class="sup_bold">(1)</sup>
        % endif
        </td>
        % for p in coll.showing_periods:
            % if p in coll:
                % data = coll[p].get("generacio", 0.0)
                <td>${_(u"%s") %(formatLang(data, digits=3))}</td>
            % else:
                <td></td>
            % endif
        % endfor
        <td>
        </td>
    </tr>
% endif
