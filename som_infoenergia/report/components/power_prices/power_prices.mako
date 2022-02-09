<%page args="d" />
<h3>${_(u"Preus del terme de potència")}</h3>
<p>${_(u"El terme de potència serà el cost regulat, sense que Som Energia apliqui cap marge ni cost afegit. Aquests preus només seran modificables per canvis normatius.")}</p>
<table>
<tr>
    <th>${_(u"Periode tarifari")}</th>
    <th>${_(u"P1")}</th>
    <th>${_(u"P2")}</th>
    <th>${_(u"P3")}</th>
    <th>${_(u"P4")}</th>
    <th>${_(u"P5")}</th>
    <th>${_(u"P6")}</th>
</tr>
% if d.tariff == '3xTD':
<tr>
    <th>${_(u"Preu 3.0TD")}</th>
    <th>16,670219</th>
    <th>12,243338</th>
    <th>5,934083</th>
    <th>5,048310</th>
    <th>3,368404</th>
    <th>2,152216</th>
</tr>
% elif d.tariff == '6xTD':
<tr>
    <th>${_(u"Preu 6.1TD")}</th>
    <th>24,732072</th>
    <th>21,529345</th>
    <th>12,319941</th>
    <th>9,897259</th>
    <th>2,833920</th>
    <th>1,571094</th>
</tr>
% endif
</table>
<p><i>${_(u"Taula 1: Preus del terme de potència per període tarifari sense impostos (€/kW i any)")}</i></p>




