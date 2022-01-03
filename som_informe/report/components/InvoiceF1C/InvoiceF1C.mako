<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> %s") % (d.distribuidora)}<br/>
    ${_(u"<b>Tipo factura:</b> Complementària (%s)") % (d.invoice_type)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Núm. de serie del EDM (Equipo de medida):</b> %s") % (d.numero_edm)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    ${_(u"<b>Concepte facturat:</b> %s") % (d.concept)}<br/>
    ${_(u"<b>Factura que complementa:</b> %s") % (d.complement_invoice)}<br/>
</li>
<br>
<br>