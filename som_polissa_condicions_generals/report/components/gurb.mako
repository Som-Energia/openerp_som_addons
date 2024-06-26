<%def name="gurb(gurb)">
    <div class="styled_box">
        <h5> ${_("SERVEI CONTRACTAT:")} ${gurb['nom']} ${_("(21 % IVA)")} </h5>
        <div class="inside_styled_box">
            <b>${_(u"Cost d'adhesió:")}</b> ${gurb['cost']} €<br/>
            <b>${_(u"Potència GURB (kW):")}</b> ${gurb['potencia']} kW <br/>
            <b>${_(u"Quota GURB (€/kW/dia):")}</b> ${gurb['quota']} ${_("€/kW/dia")} <br/>
            <b>${_(u"Beta contractada (%):")}</b> ${gurb['beta_percentatge']} %<br/>
        </div>
    </div>
</%def>
