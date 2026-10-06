<%def name="summary_header(company)">
<div class="summary-header-branding">
    <div class="summary-header-logo">
        <img class="summary-header-logo__image" src="${addons_path}/som_polissa_condicions_generals/report/assets/logo2.png"/>
    </div>
</div>
<div class="summary-title">${_(u"DOCUMENT RESUM DEL CONTRACTE DE SUBMINISTRAMENT ELÈCTRIC")}</div>
<div class="summary-box summary-box--company">
    <h3>${_(u"1. Identificació de l'empresa comercialitzadora")}</h3>
    <div class="summary-content">
        <p class="section-text"><span class="inline-label">${_(u"Denominació social:")}</span> ${company['name']}</p>
        <p class="section-text"><span class="inline-label">${_(u"Marca comercial:")}</span> ${company['brand']}</p>
        <p class="section-text"><span class="inline-label">${_(u"NIF:")}</span> ${company['vat']}</p>
        <p class="section-text"><span class="inline-label">${_(u"Adreça completa:")}</span> ${company['address']}</p>
        <p class="section-text"><span class="inline-label">${_(u"Adreça postal:")}</span> ${company['postal_address']}</p>
        <p class="section-text"><span class="inline-label">${_(u"Correu electrònic:")}</span> ${company['email']}</p>
        <p class="section-text"><span class="inline-label">${_(u"Telèfon d'atenció gratuït:")}</span> ${company['phone']}</p>
    </div>
</div>
</%def>
