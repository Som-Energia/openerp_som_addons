<%page args="ec" />
    <style>
    <%include file="emergency_complaints_td.css" />
    </style>

        <div class="emergency_td">
            <h1>${_(u"AVARIES I URGÈNCIES")}</h1>
            <p class="complaint_text">${_(u"Empresa distribuïdora:")}<br />
            <span class="padding_bold font_size_distri">${ec.distri_name}</span> <br />
            ${_(u"Núm. contracte distribuïdora:")} <span class="bold;">${ec.distri_contract}</span> <br />
            ${_(u"AVARIES I URGÈNCIES DEL SUBMINISTRAMENT (distribuïdora): ")}<span class="bold">${_(u"%s (24 hores)") % ec.distri_phone}</span><br />
            </p>
        </div>
        <div class="complaints_td">
        % if ec.is_energetica:
            <h1>${_(u"RECLAMACIONES COMERCIALIZACIÓN ENERGÉTICA/SOM ENERGIA")}</h1>
        % else:
            <h1>${_(u"RECLAMACIONS COMERCIALITZACIÓ SOM ENERGIA")}</h1>
        %endif
            <p class="complaint_text">
                % if ec.is_energetica:
                    ${_(u"Lunes a viernes, de 10 a 14h. (tardes, previa cita) 983 660 112")} <br/>
                    ${_(u"Correo electrónico: info@energetica.coop")} <br/>
                    ${_(u"Dirección postal: Avda. Ramón Pradera 12, bajo trasera; 47009-Valladolid")}
                % else:
                    ${_(u"Horari de 9 a 14 h. 900 103 605 (Gratuït. cost de la trucada per a la cooperativa).<br />"
                    u"Si tens tarifa plana de telefonia, també pots trucar-nos al %s.<br />"
                    u"Adreça electrònica: reclama@somenergia.coop<br />"
                    u"Adreça postal: C/ Riu Güell, 68 - 17005 - Girona<br />") % (ec.comer_phone,)}
                    % if ec.has_agreement_partner:
                        ${_ (u"Som Energia és la teva comercialitzadora elèctrica a mercè de l'acord firmat amb")} ${ec.agreement_partner_name} <br />
                    % endif
                % endif
                ${_(u"Pots obtenir més informació sobre reclamacions en aquest ")}
                %if ec.lang == 'ca_ES':
                    <a href="https://ca.support.somenergia.coop/article/1078-que-haig-de-fer-per-presentar-una-reclamacio">${_(u"article.")}</a>
                %else:
                    <a href="https://es.support.somenergia.coop/article/1079-que-debo-hacer-para-presentar-una-reclamacion">${_(u"article.")}</a>
                %endif
                ${_(u"Som Energia està adherida al Sistema Arbitral de Consum. Pots fer arribar la teva reclamació a la Junta Arbitral de Consum més propera: ")}
                    <a href="https://www.consumo.gob.es/es/consumo/juntasArbitrales/autonomica">aqui.</a>
            </p>
        </div>
