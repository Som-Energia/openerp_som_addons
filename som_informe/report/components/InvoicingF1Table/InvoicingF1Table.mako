<%page args="d" />
<h2>${_(u"Factures emeses per %s a Som Energia relatives al CUPS %s:") % (d.distri_name, d.cups_name)}</h2>
    <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:12%">${_(u"Número Factura")}</td>
            <td style="width:8%">${_(u"Tipus factura")}</td>
            <td style="width:13%">${_(u"Data Factura")}</td>
            <td style="width:13%">${_(u"Data inici període facturat")}</td>
            <td style="width:13%">${_(u"Data final període facturat")}</td>
            <td style="width:10%">${_(u"Dies facturats")}</td>
            <td style="width:11%">${_(u"Energia facturada (kWh)")}</td>
            <td style="width:10%">${_(u"Base import")}</td>
            <td style="width:10%">${_(u"Total import")}</td>
        </tr>
        % for f1 in reversed(d.invoices_f1_data):
            <tr style="text-align:right">
                <td style="width:12%;text-align:center">${f1['invoice_number']}</td>
                <td style="width:8%;text-align:center">${f1['invoice_type']}</td>
                <td style="width:13%;text-align:center">${f1['invoice_date']}</td>
                <td style="width:13%;text-align:center">${f1['date_from']}</td>
                <td style="width:13%;text-align:center">${f1['date_to']}</td>
                <td style="width:10%;text-align:center">${f1['invoiced_days']}</td>
                <td style="width:11%;text-align:center">${f1['invoiced_energy']}</td>
                <td style="width:10%">${_(u"%s €") % (formatLang(f1['amount_base'], digits=2))}</td>
                <td style="width:10%">${_(u"%s €") % (formatLang(f1['amount_total'], digits=2))}</td>
            </tr>
        % endfor
    </table>
    <br />
