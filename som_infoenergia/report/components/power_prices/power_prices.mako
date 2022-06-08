<%page args="d" />
<h4>${_(u"Preus del terme de potència")}</h4>
<p>${_(u"El terme de potència serà el cost regulat, sense que Som Energia apliqui cap marge ni cost afegit. Aquests preus només seran modificables per canvis normatius.")}</p>
<table>
<thead>
    <tr>
        <th>${_(u"Periode tarifari")}</th>
        <th>${_(u"P1")}</th>
        <th>${_(u"P2")}</th>
        <th>${_(u"P3")}</th>
        <th>${_(u"P4")}</th>
        <th>${_(u"P5")}</th>
        <th>${_(u"P6")}</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td>${_(u"Preu %s")} % (d.tariff)</td>
        <td>${formatLang(d.preu_p1, digits=6)}</td>
        <td>${formatLang(d.preu_p2, digits=6)}</td>
        <td>${formatLang(d.preu_p3, digits=6)}</td>
        <td>${formatLang(d.preu_p4, digits=6)}</td>
        <td>${formatLang(d.preu_p5, digits=6)}</td>
        <td>${formatLang(d.preu_p6, digits=6)}</td>
    </tr>
</tbody>
</table>
<p class="table-note">${_(u"Taula 1: Preus del terme de potència per període tarifari sense impostos (€/kW i any)")}</p>




