<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> %s") % (d.distribuidora)}<br/>
    ${_(u"<b>Tipo factura:</b> %s") % (d.invoice_type)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Núm. de serie del EDM (Equipo de medida):</b> %s") % (d.numero_edm)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:10%">${_(u"Orígen lectures")}</td>
            <td style="width:16%">${_(u"Tipus d'energia")}</td>
            <td style="width:12%">${_(u"Lectura Inicial")}</td>
            <td style="width:12%">${_(u"Lectura final")}</td>
            <td style="width:12%">${_(u"Consum entre lectures")}</td>
            <td style="width:12%">${_(u"Ajustes consumo")}</td>
            <td style="width:13%">${_(u"TOTAL kWh facturados")}</td>
        </tr>
        % for linia in d.linies:
            <tr style="text-align:right">
                <td style="width:10%;text-align:center">${_(u"%s (%s)") % (linia['description_lectures'],linia['origen_lectures'])}</td>
                <td style="width:16%;text-align:center">${_(u"Magnitud: (%s), Periode: (%s)") %(linia['magnitud'], linia['periode'])}</td>
                <td style="width:12%">${_(u"%s kWh") % (formatLang(linia['lectura_inicial'], digits=2))}</td>
                <td style="width:12%">${_(u"%s kWh") % (formatLang(linia['lectura_final'], digits=2))}</td>
                <td style="width:12%">${_(u"%s kWh") % (formatLang(linia['consum_entre'], digits=2))}</td>
                <td style="width:12%">${_(u"%s kWh") % (formatLang(linia['ajust'], digits=2))}</td>
                <td style="width:13%">${_(u"%s kWh") % (formatLang(linia['total_facturat'], digits=2))}</td>
            </tr>
        % endfor
    </table>
    <br />
</li>
