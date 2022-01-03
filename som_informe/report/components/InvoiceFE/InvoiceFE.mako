<%page args="d" />
<li>
    <h2>${_(u"Factura emesa per Som Energia relativa al CUPS %s:") % (d.cups_name)}</h2>
    ${_(u"Data Factura: %s") % (d.cups_name)}
    <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:12%">${_(u"Número Factura")}</td>
            <td style="width:12%">${_(u"Origen lectures")}</td>
            <td style="width:13%">${_(u"Data inici i lectures")}</td>
            <td style="width:13%">${_(u"Data final i lectures")}</td>
            <td style="width:10%">${_(u"Base import")}</td>
            <td style="width:10%">${_(u"Total import")}</td>
            <td style="width:13%">${_(u"Data Factura")}</td>
            <td style="width:13%">${_(u"Data venciment")}</td>
            <td style="width:11%">${_(u"Potència contractada (kW)")}</td>
            <td style="width:11%">${_(u"Energia facturada (kWh)")}</td>
            <td style="width:10%">${_(u"Dies facturats")}</td>
        </tr>
        % for fe in reversed(d.invoices_fe_data):
            <tr style="text-align:right">
                <td style="width:12%;text-align:center">${fe['invoice_number']}</td>
                <td style="width:12%;text-align:center">${fe['readings_origin']}</td>
                <td style="width:13%;text-align:center">${fe['date_from_plus_readings']}</td>
                <td style="width:13%;text-align:center">${fe['date_to_plus_readings']}</td>
                <td style="width:10%">${_(u"%s €") % (formatLang(fe['amount_base'], digits=2))}</td>
                <td style="width:10%">${_(u"%s €") % (formatLang(fe['amount_total'], digits=2))}</td>
                <td style="width:13%;text-align:center">${fe['invoice_date']}</td>
                <td style="width:13%;text-align:center">${fe['due_date']}</td>
                <td style="width:11%;text-align:center">${fe['invoiced_power']}</td>
                <td style="width:11%;text-align:center">${fe['invoiced_energy']}</td>
                <td style="width:10%;text-align:center">${fe['invoiced_days']}</td>
            </tr>
        % endfor
    </table>
    <br/>
</li>
