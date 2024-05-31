<%def name="disclaimers(polissa)">
    <div class="styled_box padding_bottom">
        <div class="center avis_impostos">
            %if (polissa['mode_facturacio'] == 'index' and not polissa['modcon_pendent_periodes']) or polissa['modcon_pendent_indexada']:
                ${_(u"Els preus del terme de potència")}
            %else:
                ${_(u"Tots els preus que apareixen en aquest contracte")}
            %endif
            &nbsp;${_(u"inclouen l'impost elèctric i l'IVA (IGIC a Canàries), amb el tipus impositiu vigent actualment per a cada tipus de contracte sense perjudici de les exempcions o bonificacions que puguin ser d'aplicació.")}
        </div>
    </div>
        <p style="page-break-after: always"></p>
        <br><br><br>
    % if polissa['bank']:
    <div class="styled_box">
        <h5> ${_("DADES DE PAGAMENT")} </h5>
        <div class="dades_pagament">
            <div class="iban"><b>${_(u"Nº de compte bancari (IBAN): **** **** **** ****")}</b> &nbsp ${polissa['printable_iban']}</div>
        </div>
    </div>
    % endif
    <div class="modi_condicions">
        <p>
            ${_(u"Al contractar s’accepten aquestes ")}
            %if (polissa['mode_facturacio'] == 'index' and not polissa['modcon_pendent_periodes']) or polissa['modcon_pendent_indexada']:
                ${_(u"Condicions Particulars, Específiques i les Condicions Generals,")}
            %else:
                ${_(u"Condicions Particulars i les Condicions Generals")}
            %endif
            ${_(u"que es poden consultar a les pàgines següents. Si ens cal modificar-les, a la clàusula 9 de les Condicions Generals s’explica el procediment que seguirem. En cas que hi hagi alguna discrepància, prevaldrà el que estigui previst en aquestes Condicions Particulars.")}
        </p>
    </div>
</%def>