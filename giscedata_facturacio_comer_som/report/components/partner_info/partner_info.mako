<%page args="pi" />
<style>
<%include file="partner_info.css" />
</style>
    <div class="partner_data">
        <div class="owner_data">
            <h1>${_(u"DADES DE LA TITULARITAT")}</h1>
            <p>${_(u"Nom del / de la titular del contracte: ")} <span style="font-weight: bold;">${pi.pol_name}</span><br />
            ${_(u"NIF/CIF:")} <span style="font-weight: bold;">${pi.vat}</span> <br /></p>
        </div>
        <div class="payment_data">
            % if pi.is_out_refund:
                <h1>${_(u"DADES D'ABONAMENT")}</h1>
            % endif
            % if not pi.is_out_refund:
                <h1>${_(u"DADES DE PAGAMENT")}</h1>
            % endif
            <p>
                ${_(u"Entitat bancària:")} <span style="font-weight: bold;">${pi.bank_name}</span> <br />
                ${_(u"Núm. compte bancari:")} <span style="font-weight: bold;">${pi.cc_name}</span> <br />
            </p>
            <hr />
            % if not pi.is_out_refund:
                % if pi.payment_type != 'TRANSFERENCIA_CSB':
                    <p style="font-size: .8em">${_(u"L'import d'aquesta factura es carregarà al teu compte. El seu pagament queda justificat amb l'apunt bancari corresponent.")}</p>
                % else:
                    <p style="font-size: .8em">${_(u"L'import d'aquesta factura es pagarà mitjançant transferència bancària al compte indicat.")}</p>
                % endif
            % endif
        </div>
    </div>
