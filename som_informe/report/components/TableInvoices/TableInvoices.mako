<%page args="d" />
% if False:
    ${_(u"sense lectura")}
% endif
${_(u"<b>A continuació es mostra un resum de les factures emeses per Som Energia al titular de contracte pel període (%s - %s): </b>") % (d.date_from , d.date_to)}<br/>
<br>
<br>
<table style="width:100%;font-size:14px">
    <tr style="text-align:center;font-weight:bold">
        <td style="width:17%">${_(u"Número factura")}</td>
        <td style="width:10%">${_(u"Data factura")}</td>
        <td style="width:10%">${_(u"Data inici període facturat")}</td>
        <td style="width:10%">${_(u"Data final període facturat")}</td>
        <td style="width:10%">${_(u"Màxima Potència contractada (kW)")}</td>
        <td style="width:10%">${_(u"Energia facturada (kWh)")}</td>
        <td style="width:10%">${_(u"Energia exportada -excedents- (kWh)")}</td>
        <td style="width:10%">${_(u"Origen consum")}</td>
        <td style="width:10%">${_(u"Dies facturats")}</td>
        <td style="width:10%">${_(u"Import total (€)")}</td>
    </tr>
    % for linia in d.taula:
        <tr style="text-align:center">
            <td style="width:17%">${_(u"%s") %(linia['invoice_number'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['date'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['date_from'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['date_to'])}</td>
            <td style="width:10%">${_(u"%s") % (formatLang(linia['max_power'], digits=3))}</td>
            <td style="width:10%">${_(u"%s") % (formatLang(linia['invoiced_energy'], digits=2))}</td>
            <td style="width:10%">${_(u"%s") % (formatLang(linia['exported_energy'], digits=2))}</td>
            <td style="width:10%">${_(u"%s") % (linia['origin'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['invoiced_days'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['total'])}</td>
        </tr>
    % endfor
</table>
<br>
<br>
