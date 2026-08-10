<%def name="summary_payment(payment)">
<div class="summary-box">
    <h3>${_(u"4. Dades de pagament")}</h3>
    <div class="summary-content">
        <p class="section-text"><span class="inline-label">${_(u"Nre. de compte bancari seleccionat (IBAN) / Targeta de crèdit:")}</span>
            %if payment['is_card'] and not payment['last4']:
                ${_(u"Targeta de crèdit (pagament seleccionat mitjançant targeta bancària)")}
            %else:
                ${payment['label']}
            %endif
        </p>
    </div>
</div>
</%def>
