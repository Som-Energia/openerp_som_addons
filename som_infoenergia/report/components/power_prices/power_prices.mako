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
        <td>14,440099</td>
        <td>11,127305</td>
        <td>5,123259</td>
        <td>4,237486</td>
        <td>2,557580</td>
        <td>1,780529</td>
    </tr>
    % elif d.tariff == '6xTD':
    <tr>
        <td>${_(u"Preu 6.1TD")}</td>
        <td>22,417110</td>
        <td>20,370815</td>
        <td>11,478137</td>
        <td>9,055455</td>
        <td>1,992116</td>
        <td>1,185268</td>
    </tr>
    % endif
</tbody>
</table>
<p class="table-note">${_(u"Taula 1: Preus del terme de potència per període tarifari sense impostos (€/kW i any)")}</p>




