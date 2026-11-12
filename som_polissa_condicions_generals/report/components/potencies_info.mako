<%def name="potencies_info(polissa, potencies)">
    <div class="peatge_acces styled_box">
        <h5> ${_(u"PEATGE I CÀRRECS (definits a la Circular de la CNMC 3/2020 i al Reial decret 148/2021)")} </h5>
        <div class="peatge_access_content">
            <div class="padding_left"><b>${_(u"Peatge de transport i distribució: ")}</b>${polissa['tarifa']}</div>
            <div class="padding_left"><b>${_(u"Tipus de contracte: ")}</b> ${polissa['contract_type']} ${"({0})".format(potencies['autoconsum']) if polissa['auto'] != '00' else ""}</div>
            <div class="padding_bottom padding_left"><b>${_(u"Tarifa: ")}</b> ${polissa['tarifa_mostrar']}</div>
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
                    <td class="bold">${_(u"Potència contractada (kW):")}</td>
                    %for p in potencies['periodes']:
                        <td class="center">
                        %if p and p[1]:
                            <span>${formatLang(p[1] / 1000.0 if potencies['es_canvi_tecnic'] else p[1], digits=3)}</span>
                        %endif
                        </td>
                    %endfor
                </tr>
            </table>
        </div>
    </div>
</%def>
