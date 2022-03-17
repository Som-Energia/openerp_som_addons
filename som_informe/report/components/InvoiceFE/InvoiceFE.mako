<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> Som Energia")}<br/>
    ${_(u"<b>Tipo factura:</b> Factura cliente")}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Núm. de serie del EDM (Equipo de medida):</b> %s") % (d.numero_edm)}<br/>
    ${_(u"<b>Dies facturats:</b> %s") % (d.invoiced_days)}<br/>
    ${_(u"<b>Import total:</b> %s") % (d.amount_total)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    ${_(u"<b>Concepte facturat:</b> %s") % (d.concept)}<br/>
    ${_(u"<b>Factura que anula o rectifica:</b> %s") % (d.complement_invoice)}<br/>
    ${_(u"<b>Número expedient:</b> %s") % (d.num_expedient)}<br/>

</li>
<br>
<br>