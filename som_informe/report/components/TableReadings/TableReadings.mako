<%page args="d" />
<table style="width:100%;font-size:14px">
    <tr style="text-align:center;font-weight:bold">
        <td style="width:14%">${_(u"Número factura")}</td>
        <td style="width:14%">${_(u"Codi fiscal factura")}</td>
        <td style="width:10%">${_(u"Data inici període facturat")}</td>
        <td style="width:10%">${_(u"Data final període facturat")}</td>
        <td style="width:10%">${_(u"Data factura")}</td>
        <td style="width:10%">${_(u"Energia facturada (kWh)")}</td>
        <td style="width:10%">${_(u"Energia exportada -excedents- (kWh)")}</td>
        <td style="width:9%">${_(u"Dies facturats")}</td>
    </tr>
    % for linia in d:
        <tr style="text-align:center">
            <td style="width:14%">${_(u"%s %s") %(linia['invoice_number'])}</td>
            <td style="width:14%">${_(u"%s") % (linia['invoice_code'])}</td>
            <td style="width:10%">${_(u"%s %s") % (linia['date_from'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['date_to'])}</td>
            <td style="width:10%">${_(u"%s %s") % (linia['date'])}</td>
            <td style="width:10%">${_(u"%s %s") % (formatLang(linia['invoiced_energy'], digits=2))}</td>
            <td style="width:10%">${_(u"%s %s") % (formatLang(linia['exported_energy'], digits=2))}</td>
            <td style="width:9%">${_(u"%s %s") % (linia['invoiced_days'])}</td>
        </tr>
    % endfor
</table>
<br>
<br>