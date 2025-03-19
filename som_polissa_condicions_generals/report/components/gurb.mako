<%def name="gurb(gurb)">
    <div class="styled_box">
        <h5> ${_(u"SERVEI CONTRACTAT:")} ${gurb['nom']} ${_(u"(21 % IVA)")} </h5>
        <div class="inside_styled_box">
            <b>${_(u"Cost d'adhesió:")}</b> 50 €<br/>
            <b>${_(u"Potència GURB (kW):")}</b> ${gurb['potencia']} kW <br/>
            <b>${_(u"Quota GURB (€/kW/dia):")}</b> ${gurb['quota']} ${_(u"€/kW/dia")} <br/>
            <b>${_(u"Beta contractada (%):")}</b> ${gurb['beta_percentatge']} %<br/>
        </div>
    </div>
</%def>
