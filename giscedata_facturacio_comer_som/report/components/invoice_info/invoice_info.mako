<%page args="ii" />
<style>
<%include file="invoice_info.css" />
</style>
        <h1 class="${ii.has_agreement_partner and 'agreement' or ''}partner">${_(u"DADES DE LA FACTURA")}</h1>
         <div style="font-weight: 900;font-size: 1.3em">${_(u"IMPORT DE LA FACTURA:  %s &euro;") % formatLang(ii.amount_total)}
         % if ii.type == 'out_refund':
             (${_(u"ABONAMENT")})
         % endif
         </div>
        <p>${_(u"Núm. de factura:")} <span style="font-weight: bold;">${ii.number}</span> <br />
        % if ii.type == 'out_refund' and ii.ref:
            ${_(u"Aquesta factura anul·la la factura")} ${ii.ref_number} <br />
        % endif
        ${_(u"Data de la factura:")} <span style="font-weight: bold;">${ii.date_invoice}</span> <br />
        ${_(u"Període facturat:")} <span style="font-weight: bold;">${_(u"del %s al %s") % (ii.start_date, ii.end_date)}</span> <br />
        ${_(u"Data venciment de la factura:")} <span style="font-weight: bold;">${ii.due_date}</span> <br />
        ${_(u"Núm. de contracte:")} <span style="font-weight: bold;">${ii.contract_number}</span> <br />
        ${_(u"Adreça de subministrament:")} <span style="font-weight: bold;">${ii.address}</span> <br />
        </p>
        <div class="${ii.has_agreement_partner and 'agreement' or ''}partner" style="height: 2px; padding: 0px;"></div>
