<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> Som Energia")}<br/>
    ${_(u"<b>Tipus factura:</b> %s") % (d.tipo_factura)}<br/>
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    ${_(u"<b>Núm. de sèrie de l'EdM (Equip de Mesura):</b> %s") % (d.numero_edm)}<br/>
    ${_(u"<b>Dies facturats:</b> %s") % (d.invoiced_days)}<br/>
    ${_(u"<b>Potència:</b>")}
    %if len(d.potencies) == 2:
        ${_(u"Punta: %s; Vall %s") % (d.potencies[0]['potencia'],d.potencies[1]['potencia'])}<br/>
    %elif d.potencies:
        % for pot in d.potencies[:-1]:
            ${_(u"%s : %s;") % (pot['periode'], pot['potencia'])}
        %endfor
        ${_(u"%s : %s") % (d.potencies[-1]['periode'], d.potencies[-1]['potencia'])}<br/>
    %endif
    ${_(u"<b>Import total:</b> %s €") % (d.amount_total)}<br/>
    ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
    ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
    %if d.other_concepts:
        ${_(u"<b>Altres conceptes facturats:</b>")}<br/>
        % for concept in d.other_concepts:
            ${_(u"%s %s €") % (concept['name'], concept['price'])}<br/>
        %endfor
    %endif
     <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:15%">${_(u"Tipus d'energia")}</td>
            <td style="width:12%">${_(u"Origen lectura inicial")}</td>
            <td style="width:12%">${_(u"Lectura Inicial (kWh)")}</td>
            <td style="width:12%">${_(u"Origen lectura final")}</td>
            <td style="width:12%">${_(u"Lectura final (kWh)")}</td>
            <td style="width:12%">${_(u"Consum entre lectures (kWh)")}</td>
            <td style="width:12%">${_(u"Origen consum facturat")}</td>
            <td style="width:13%">${_(u"TOTAL facturat (kWh)")}</td>
        </tr>
    % for lectura in d.lectures:
        <tr style="text-align:right">
            <td style="width:15%;text-align:center">${_(u"%s %s") %(lectura['magnitud_desc'],lectura['periode_desc'])}</td>
            <td style="width:12%;text-align:center">${_(u"%s") % (lectura['origen_lectura_inicial'])}</td>
            <td style="width:12%">${_(u"%s") % (formatLang(lectura['lectura_inicial'], digits=2))}</td>
            <td style="width:12%;text-align:center">${_(u"%s") % (lectura['origen_lectura_final'])}</td>
            <td style="width:12%">${_(u"%s") % (formatLang(lectura['lectura_final'], digits=2))}</td>
            <td style="width:12%">${_(u"%s") % (formatLang(lectura['consum_entre'], digits=2))}</td>
            <td style="width:12%;text-align:center">${_(u"%s") % (lectura['origen'])}</td>
            <td style="width:13%">${_(u"%s") % (formatLang(lectura['total_facturat'], digits=2))}</td>
        </tr>
    %endfor
    </table>
    %if d.maximetre:
        <br>
        <br>
        <table style="width:100%;font-size:14px">
            <tr style="text-align:center;font-weight:bold">
                <td style="width:15%">${_(u"Període maxímetre")}</td>
                <td style="width:15%">${_(u"Potència contractada")}</td>
                <td style="width:15%">${_(u"Potència maxímetre")}</td>
                <td style="width:15%">${_(u"Potència excedida")}</td>
            </tr>
        % for lectura_maximetre in d.lectures_maximetre:
            <tr style="text-align:right">
                <td style="width:15%;text-align:center">${_(u"%s") %(lectura_maximetre['periode'])}</td>
                <td style="width:15%">${_(u"%s") % (formatLang(lectura_maximetre['pot_contractada'], digits=2))}</td>
                <td style="width:15%">${_(u"%s") % (formatLang(lectura_maximetre['pot_maximetre'], digits=2))} </td>
                <td style="width:15%">${_(u"%s") % (formatLang(lectura_maximetre['exces'], digits=2))}</td>
            </tr>
        %endfor
        </table>
    %endif
</li>
<br>
<br>
