<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> %s") % (d.distribuidora)}<br/>
    ${_(u"<b>Tipus factura:</b> Complementària (%s)") % (d.invoice_type)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    ${_(u"<b>Tipus de factura:</b> %s") % (d.concept)}<br/>
    ${_(u"<b>Número expedient:</b> %s") % (d.num_expedient)}<br/>
    ${_(u"<b>Comentaris:</b> %s") % (d.comentaris)}<br/>
    <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:14%">${_(u"Descripció")}</td>
            <td style="width:16%">${_(u"Tipus")}</td>
            <td style="width:12%">${_(u"Quantitat")}</td>
            <td style="width:10%">${_(u"Unitat de mesura")}</td>
        </tr>
        % for linia in d.linies:
            <tr style="text-align:right">
                <td style="width:14%">${_(u"%s") % (linia['name'])}</td>
                <td style="width:16%">${_(u"%s") % (linia['tipus'])}</td>
                <td style="width:12%">${_(u"%s") % (formatLang(linia['quantity'], digits=3))}</td>
                <td style="width:10%">${_(u"%s") % (linia['uom'])}</td>
            </tr>
        % endfor
    </table>
</li>
<br>
<br>
