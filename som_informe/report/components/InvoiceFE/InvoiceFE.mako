<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> Som Energia")}<br/>
    ${_(u"<b>Tipus factura:</b> %s") % (d.tipo_factura)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Núm. de sèrie del EdM (Equip de Mesura):</b> %s") % (d.numero_edm)}<br/>
    ${_(u"<b>Dies facturats:</b> %s") % (d.invoiced_days)}<br/>
    ${_(u"<b>Potència:</b>")}
    %if len(d.potencies) == 2:
        ${_(u"Punta: %s; Vall %s") % (d.potencies[0].potencia,d.potencies[1].potencia)}<br/>
    %else:
        % for pot in d.potencies[:-1]:
            ${_(u"%s : %s;") % (pot.periode, pot.potencia)}
        %endfor
        ${_(u"%s : %s") % (potencies[-1].periode, potencies[-1].potencia)}<br/>
    %endif
    ${_(u"<b>Import total:</b> %s") % (d.amount_total)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    %if d.other_concepts:
        ${_(u"<b>Otros conceptos facturados:</b>")}<br/>
        % for concept in d.other_concepts:
            ${_(u"%s %s €") % (concept.name, concept.price)}<br/>
        %endfor
    %endif
     <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:12%">${_(u"Tipus d'energia")}</td>
            <td style="width:9%">${_(u"Orígen lectura inicial")}</td>
            <td style="width:10%">${_(u"Lectura Inicial")}</td>
            <td style="width:9%">${_(u"Orígen lectura final")}</td>
            <td style="width:10%">${_(u"Lectura final")}</td>
            <td style="width:12%">${_(u"Consum entre lectures")}</td>
            <td style="width:12%">${_(u"Origen consum facturat")}</td>
            <td style="width:13%">${_(u"TOTAL facturat")}</td>
        </tr>
    %for lectura in d.lectures:
        <tr style="text-align:right">
            <td style="width:12%;text-align:center">${_(u"%s %s") %(linia['magnitud_desc'],linia['periode_desc'])}</td>
            <td style="width:9%;text-align:center">${_(u"%s") % (linia['origen_lectura_inicial'])}</td>
            <td style="width:10%">${_(u"%s") % (formatLang(linia['lectura_inicial'], digits=2))}</td>
            <td style="width:9%;text-align:center">${_(u"%s") % (linia['origen_lectura_final'])}</td>
            <td style="width:10%">${_(u"%s") % (formatLang(linia['lectura_final'], digits=2))}</td>
            <td style="width:12%">${_(u"%s") % (formatLang(linia['consum_entre'], digits=2))}</td>
            <td style="width:12%">${_(u"%s") % (linia['origen'])}</td>
            <td style="width:12%">${_(u"%s") % (formatLang(linia['total_facturat'], digits=2))}</td>
        </tr>
    %endfor
    </table>
</li>
<br>
<br>