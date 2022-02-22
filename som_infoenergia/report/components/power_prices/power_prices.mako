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
    % if d.tariff == '3xTD':
    <tr>
        <td>${_(u"Preu 3.0TD")}</td>
        <td>16,670219</td>
        <td>12,243338</td>
        <td>5,934083</td>
        <td>5,048310</td>
        <td>3,368404</td>
        <td>2,152216</td>
    </tr>
    % elif d.tariff == '6xTD':
    <tr>
        <td>${_(u"Preu 6.1TD")}</td>
        <td>24,732072</td>
        <td>21,529345</td>
        <td>12,319941</td>
        <td>9,897259</td>
        <td>2,833920</td>
        <td>1,571094</td>
    </tr>
    % endif
</tbody>
</table>
<p class="table-note">${_(u"Taula 1: Preus del terme de potència per període tarifari sense impostos (€/kW i any)")}</p>




