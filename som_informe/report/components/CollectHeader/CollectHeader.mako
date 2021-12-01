<%page args="d" />

% if d.is_enterprise:
    <h2>${_(u"Gestió de cobraments:")}</h2>
% else:
    <h2>${_(u"Gestió de cobraments i situació de vulnerabilitat energètica:")}</h2>
% endif
    ${_(u"Actualment, al contracte %s hi ha %d factures pendents de pagament. El deute total acumulat és de %s €. A continuació us detallem la relació de factures que han generat impagaments: ") % (d.contract_number, d.unpaid_invoices, formatLang(d.unpaid_amount,digits=2) )} <br />
    <br />
