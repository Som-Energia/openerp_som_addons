<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> %s") % (d.distribuidora)}<br/>
    %if d.invoice_type == 'R':
    ${_(u"<b>Tipo factura:</b> Rectificativa (%s)") % (d.invoice_type)}<br/>
    %else:
    ${_(u"<b>Tipo factura:</b> Anul·ladora (%s)") % (d.invoice_type)}<br/>
    %endif
    ${_(u"<b>Tipo factura:</b> %s") % (d.invoice_type)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Núm. de serie del EDM (Equipo de medida):</b> %s") % (d.numero_edm)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    ${_(u"<b>Concepte facturat:</b> %s") % (d.concept)}<br/>
    ${_(u"<b>Factura que anula o rectifica:</b> %s") % (d.rectifies_invoice)}<br/>
</li>
<br>
<br>