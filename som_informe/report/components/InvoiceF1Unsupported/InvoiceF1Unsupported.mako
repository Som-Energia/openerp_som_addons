<%page args="d" />
<li>
    ${_(u"<b>Tipus de factura no suportat</b>")}<br/>
    ${_(u"<b>Tipus factura:</b> %s") % (d.invoice_type)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Id factura:</b> %s") % (d.invoice_id)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
</li>
<br>
<br>
