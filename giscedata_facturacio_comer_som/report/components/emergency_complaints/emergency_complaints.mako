<%page args="ec,location" />
% if location == ec.location:
    <style>
    <%include file="emergency_complaints.css" />
    </style>
        <%
            fixed_height = ''
        %>
        % if ec.is_6X:
        <div class="row">
            <div class="column">
            <%
                fixed_height = 'style="height: 100px"'
            %>
        % endif
                <div class="emergency" ${fixed_height}>
                    <h1>${_(u"AVARIES I URGÈNCIES")}</h1>
                    <p style="line-height: 1.0;">${_(u"Empresa distribuïdora:")} <span style="font-weight: bold;">${ec.distri_name}</span> <br />
                    ${_(u"Núm. contracte distribuïdora:")} <span style="font-weight: bold;">${ec.distri_contract}</span> <br />
                    ${_(u"AVARIES I URGÈNCIES DEL SUBMINISTRAMENT (distribuïdora): %s (24 hores)") % ec.distri_phone}<br />
                    </p>
                </div>
        % if ec.is_6X:
        </div>
        <div class="column">
        % endif
        <div class="complaints" ${fixed_height}>
            <h1>${_(u"RECLAMACIONS")}</h1>
            <p style="line-height: 1.0;">
                % if ec.is_energetica:
                    ${_(u"RECLAMACIONES COMERCIALIZACIÓN (ENERGÉTICA/SOM ENERGIA): Lunes a viernes, de 10 a 14h. (tardes, previa cita) 983 660 112")} <br/>
                    ${_(u"Correo electrónico: info@energetica.coop")} <br/>
                    ${_(u"Dirección postal: Avda. Ramón Pradera 12, bajo trasera; 47009-Valladolid")}
                % else:
                    ${_(u"RECLAMACIONS COMERCIALITZACIÓ (SOM ENERGIA): Horari d'atenció de 9 a 14 h. 900 103 605 (cost de la trucada per a la cooperativa).<br />"
                    u"Si tens tarifa plana, pots contactar igualment al %s, sense cap cost.<br />"
                    u"Adreça electrònica: reclama@somenergia.coop<br />"
                    u"Adreça postal: C/ Riu Güell, 68 - 17005 - Girona<br />") % (ec.comer_phone,)}
                    % if ec.has_agreement_partner:
                        ${_ (u"Som Energia és la teva comercialitzadora elèctrica a mercè de l'acord firmat amb")} ${ec.agreement_partner_name} <br />
                    % endif
                % endif
                ${_(u"Som Energia està adherida al Sistema Arbitral de Consum. Pots fer arribar la teva reclamació a la Junta Arbitral de Consum més propera: ")}
                    <a href="https://www.consumo.gob.es/es/consumo/juntasArbitrales/autonomica">aqui.</a>
            </p>
        </div>
        % if ec.is_6X:
            </div>
            </div>
        % endif
% endif
