<%page args="d" />
${_(u"<b>A continuació es mostra un resum de les factures emeses per %s (fitxers F1) a Som Energia pel període (%s - %s): </b>") % (d.distribuidora, d.date_from , d.date_to)}<br/>
<br>
<br>
<table style="width:100%;font-size:14px">
    <tr style="text-align:center;font-weight:bold">
        <td style="width:17%">${_(u"Número factura")}</td>
        <td style="width:10%">${_(u"Tipus de factura")}</td>
        <td style="width:10%">${_(u"Data factura")}</td>
        <td style="width:10%">${_(u"Data inici període facturat")}</td>
        <td style="width:10%">${_(u"Data final període facturat")}</td>
        <td style="width:10%">${_(u"Energia facturada (kWh)")}</td>
        <td style="width:10%">${_(u"Energia exportada -excedents- (kWh)")}</td>
        <td style="width:10%">${_(u"Dies facturats")}</td>
        <td style="width:10%">${_(u"Factura que anul·la o rectifica")}</td>
    </tr>
    % for linia in d.taula:
        <tr style="text-align:center">
            <td style="width:17%">${_(u"%s") %(linia['invoice_number'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['tipus_factura'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['date'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['date_from'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['date_to'])}</td>
            <td style="width:10%">${_(u"%s") % (formatLang(linia['invoiced_energy'], digits=2))}</td>
            <td style="width:10%">${_(u"%s") % (formatLang(linia['exported_energy'], digits=2))}</td>
            <td style="width:10%">${_(u"%s") % (linia['invoiced_days'])}</td>
            <td style="width:10%">${_(u"%s") % (linia['rectifying_invoice'])}</td>
        </tr>
    % endfor
</table>
<br>
${_(u"Informació sobre els possibles tipus de factura que envia l’empresa distribuïdora:")}<br/>
${_(u"<b>Factura Normal:</b> document per facturar un cicle de facturació típic.")}<br/>
${_(u"<b>Factura Anul·ladora (A):</b> anul·la una factura que mai s’hauria d'haver emès.")}<br/>
${_(u"<b>Factura Rectificadora (R):</b> substitueix una factura ja emesa (correctament emesa) per al mateix període de facturació motivada per un millor valor d'algun concepte a facturar.")}<br/>
${_(u"<b>Factura Complementària (C):</b> Complementa una altra/es factura/es que no s'anul·la/en motivada per l'incorrecte registre de la mesura.")}<br/>
${_(u"<b>Factura Regularitzadora (G):</b> modifica una o diverses factures ja emeses que no s'anul·len.")}<br/>
<br>
<br>
