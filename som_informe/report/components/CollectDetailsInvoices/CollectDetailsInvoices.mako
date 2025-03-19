<%page args="d" />
    <table style="width:100%;font-size:14px">
        <tr style="text-align:center;font-weight:bold">
            <td style="width:16%">${_(u"Número Factura")}</td>
            <td style="width:12%">${_(u"Data inici període facturat")}</td>
            <td style="width:12%">${_(u"Data final període facturat")}</td>
            <td style="width:12%">${_(u"Data Factura")}</td>
            <td style="width:12%">${_(u"Data gir bancari")}</td>
            <td style="width:12%">${_(u"Data de la devolució")}</td>
            <td style="width:12%">${_(u"Total import")}</td>
            <td style="width:12%">${_(u"Import pendent")}</td>
        </tr>
        % for invoice in d.invoices_data:
            <tr style="text-align:right">
                <td style="width:16%">${invoice['invoice_number']}</td>
                <td style="width:12%">${invoice['data_inici']}</td>
                <td style="width:12%">${invoice['data_final']}</td>
                <td style="width:12%">${invoice['invoice_date']}</td>
                <td style="width:12%">${invoice['due_date']}</td>
                <td style="width:12%">${invoice['devolucio_date']}</td>
                <td style="width:12%">${_(u"%s €") % (formatLang(invoice['amount_total'], digits=2))}</td>
                <td style="width:12%">${_(u"%s €") % (formatLang(invoice['pending_amount'], digits=2))}</td>
            </tr>
        % endfor
    </table>
    <br />
