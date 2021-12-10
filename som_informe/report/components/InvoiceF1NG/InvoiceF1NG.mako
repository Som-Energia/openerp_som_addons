<%page args="d" />
<li>
    <!--h2>${_(u"Factures emesa per %s a Som Energia relativa al CUPS %s:") % (d.distri_name, d.cups_name)}</h2-->
     ${_(u"<b>Núm. de serie del EDM (Equipo de medida):</b> %s") % (d.numero_edm)}<br/>
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
        <tr style="text-align:right">
            <td style="width:12%;text-align:center">${d.invoice_number}</td>
            <td style="width:8%;text-align:center">${d.invoice_type}</td>
            <td style="width:13%;text-align:center">${d.invoice_date}</td>
            <td style="width:13%;text-align:center">${d.date_from}</td>
            <td style="width:13%;text-align:center">${d.date_to}</td>
            <td style="width:10%;text-align:center">${d.invoiced_days}</td>
            <td style="width:11%;text-align:center">${d.invoiced_energy}</td>
            <td style="width:10%">${_(u"%s €") % (formatLang(d.amount_base, digits=2))}</td>
            <td style="width:10%">${_(u"%s €") % (formatLang(d.amount_total, digits=2))}</td>
        </tr>
    </table>
    <br />
</li>
