<%page args="d" />
<li>
    ${_(u"<b>Emissor:</b> %s") % (d.distribuidora)}<br/>
    %if d.invoice_type == 'N':
    ${_(u"<b>Tipus factura:</b> Normal (%s)") % (d.invoice_type)}<br/>
    %else:
    ${_(u"<b>Tipus factura:</b> Regularitzadora (%s)") % (d.invoice_type)}<br/>
    %endif
    ${_(u"<b>Data factura:</b> %s") % (d.invoice_date)}<br/>
    ${_(u"<b>Número factura:</b> %s") % (d.invoice_number)}<br/>
    %if d.type_f1 == 'atr':
        ${_(u"<b>Núm. de sèrie de l'EdM (Equip de Mesura):</b> %s") % (d.numero_edm)}<br/>
        ${_(u"<b>Inici període:</b> %s") % (d.date_from)}<br/>
        ${_(u"<b>Fi període:</b> %s") % (d.date_to)}<br/>
        <table style="width:100%;font-size:14px">
            <tr style="text-align:center;font-weight:bold">
                <td style="width:12%">${_(u"Tipus d'energia")}</td>
                <td style="width:9%">${_(u"Origen lectura inicial")}</td>
                <td style="width:10%">${_(u"Lectura Inicial")}</td>
                <td style="width:9%">${_(u"Origen lectura final")}</td>
                <td style="width:10%">${_(u"Lectura final")}</td>
                <td style="width:12%">${_(u"Consum entre lectures")}</td>
                <td style="width:12%">${_(u"Ajustos consum")}</td>
                <td style="width:13%">${_(u"TOTAL facturat")}</td>
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
                    %if linia['magnitud_desc'] == 'Excesos de potencia':
                        <td style="width:13%">${_(u"%s %s") % (formatLang(linia['total_facturat'], digits=2), '€')}</td>
                    %else:
                        <td style="width:13%">${_(u"%s %s") % (formatLang(linia['total_facturat'], digits=2), linia['unit'])}</td>
                    %endif
                </tr>
            % endfor
        </table>
    %else:
        ${_(u"<b>Tipus de factura:</b> %s") % (d.concept)}<br/>
        <table style="width:100%;font-size:14px">
            <tr style="text-align:center;font-weight:bold">
                <td style="width:50%">${_(u"Descripció")}</td>
                <td style="width:56%">${_(u"Total")}</td>
            </tr>
        % for linia_extra in d.linies_extra:
            <tr style="text-align:right">
                <td style="width:50%">${_(u"%s") % (linia_extra['name'])}</td>
                <td style="width:50%">${_(u"%s €") %(linia_extra['total'])}</td>
            </tr>
        % endfor
        </table>
    %endif
</li>
<br>
<br>
