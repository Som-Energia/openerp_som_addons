<%def name="footer(polissa)">
    <div id="footer">
        <div class="city_date">
        <%
            data_firma =  datetime.today()
        %>
            ${company.partner_id.address[0]['city']},
            ${_(u"a {0}".format(localize_period(data_firma, lang)))}
        </div>
        <div class="acceptacio_digital">
            % if polissa['is_business']:
                <div><b>${_(u"La contractant")}</b></div>
            % else:
                <div><b>${_(u"La persona clienta:")}</b></div>
            % endif

            %if not polissa['lead']:
                <img src="${addons_path}/som_polissa_condicions_generals/report/assets/acceptacio_digital.png"/>
            %endif

            % if polissa['is_business']:
                <div class="acceptacio_digital_txt">${_(u"Signat digitalment")}</div>
            % elif not polissa['lead']:
                <div class="acceptacio_digital_txt">${_(u"Acceptat digitalment via formulari web")}</div>
            % endif

            <div><b>${polissa.pagador.name if not pas01 else dict_titular['client_name']}</b></div>
        </div>
        <div class="signatura">
            <div><b>${_(u"La comercialitzadora")}</b></div>
            <img src="${addons_path}/som_polissa_condicions_generals/report/assets/signatura_contracte.png"/>
            <div><b>${company.name}</b></div>
        </div>
        <div class="observacions">
            ${polissa.print_observations or ""}
        </div>
    </div>
    %if polissa['state'] == 'esborrany':
        <div class="esborrany_footer">
            <p>
                ${_(u"Aquestes Condicions Particulars estan condicionades a possibles modificacions amb la finalitat d'ajustar-les a les condicions tècniques d'accés a xarxa segons la clàusula 6.3 de les Condicions Generals.")}
            </p>
        </div>
    %endif
</%def>