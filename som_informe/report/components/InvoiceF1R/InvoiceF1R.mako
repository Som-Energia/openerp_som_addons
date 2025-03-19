<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> %s") % (d.distribuidora)}<br/>
    ${_(u"<b>Tipus factura:</b> Rectificadora (%s)") % (d.invoice_type)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Núm. de sèrie de l'EdM (Equip de Mesura):</b> %s") % (d.numero_edm)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    ${_(u"<b>Factura que rectifica:</b> %s") % (d.rectifies_invoice)}<br/>
    <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:12%">${_(u"Tipus d'energia")}</td>
            <td style="width:9%">${_(u"Origen lectura inicial")}</td>
            <td style="width:10%">${_(u"Lectura Inicial")}</td>
            <td style="width:9%">${_(u"Origen lectura final")}</td>
            <td style="width:10%">${_(u"Lectura final")}</td>
            <td style="width:12%">${_(u"Consum entre lectures")}</td>
            <td style="width:12%">${_(u"Ajustes consumo")}</td>
            <td style="width:13%">${_(u"TOTAL facturado")}</td>
        </tr>
        % for linia in d.linies:
            <tr style="text-align:right">
                <td style="width:12%;text-align:center">${_(u"%s %s") %(linia['magnitud_desc'],linia['periode_desc'])}</td>
                <td style="width:9%;text-align:center">${_(u"%s") % (linia['origen_lectura_inicial'])}</td>
                <td style="width:10%">${_(u"%s %s") % (formatLang(linia['lectura_inicial'], digits=2), linia['unit'])}</td>
                <td style="width:9%;text-align:center">${_(u"%s") % (linia['origen_lectura_final'])}</td>
                <td style="width:10%">${_(u"%s %s") % (formatLang(linia['lectura_final'], digits=2), linia['unit'])}</td>
                <td style="width:12%">${_(u"%s %s") % (formatLang(linia['consum_entre'], digits=2), linia['unit'])}</td>
                <td style="width:12%">${_(u"%s %s") % (formatLang(linia['ajust'], digits=2), linia['unit'])}</td>
                %if linia['magnitud_desc'] != 'Excesos de potencia':
                    <td style="width:13%">${_(u"%s %s") % (formatLang(linia['total_facturat'], digits=2), linia['unit'])}</td>
                %else:
                    <td style="width:13%">${_(u"%s %s") % (formatLang(linia['total_facturat'], digits=2), '€')}</td>
                %endif
            </tr>
        % endfor
    </table>
</li>
<br>
<br>
