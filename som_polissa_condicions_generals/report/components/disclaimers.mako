<%def name="disclaimers(polissa, prices)">
    <div class="modi_condicions">
        <p>
            ${_(u"Al contractar s'accepten aquestes ")}
            %if (polissa['mode_facturacio'] == 'index' and not polissa['modcon_pendent_periodes'] and not polissa['auvi']) or polissa['modcon_pendent_indexada']:
                ${_(u"Condicions Particulars, Específiques i les Condicions Generals,")}
            %elif prices['auvi']:
                ${_(u"Condicions Particulars, Específiques de l'Autoconsum Virtual, Específiques de la tarifa Indexada i les Condicions Generals,")}
            %else:
                ${_(u"Condicions Particulars i les Condicions Generals,")}
            %endif
            ${_(u"que es poden consultar a les pàgines següents. Si ens cal modificar-les, a la clàusula 9 de les Condicions Generals s'explica el procediment que seguirem. En cas que hi hagi alguna discrepància, prevaldrà el que estigui previst en aquestes Condicions Particulars.")}
        </p>
    </div>
</%def>
