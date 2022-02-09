<%page args="d" />
<h3>${_(u"Preus del terme de potència")}</h3>
<p>${_(u"El terme de potència serà el cost regulat, sense que Som Energia apliqui cap marge ni cost afegit. Aquests preus només seran modificables per canvis normatius.")}</p>
<table>
<tr>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
</tr>
% if d.tariff == '3xTD':
<tr>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
</tr>
% endif
% if d.tariff == '6xTD':
<tr>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
    <th></th>
</tr>
% endif
</table>
<p><i>${_(u"Taula 1: Preus del terme de potència per període tarifari sense impostos (€/kW i any)")}</i></p>




