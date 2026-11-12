<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> %s") % (d.distribuidora)}<br/>
    ${_(u"<b>Tipus factura:</b> Anul·ladora (%s)") % (d.invoice_type)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Factura que anul·la:</b> %s") % (d.cancel_invoice)}<br/>
</li>
<br>
<br>
