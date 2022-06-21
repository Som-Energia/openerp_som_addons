<%page args="d" />
<h4>${_(u"Preus del terme d’energia")}</h4>
<p>${_(u"En el terme d’energia es presenta una oferta indexada en relació amb els preus de mercat diari. La tarifa indexada es calcula mitjançant la següent fórmula:")}</p>
<p class="center"><b>${_(u"PH = 1,015 * [(PHM + PHMA + Pc + SobrecostosREE + Interrump + P<sub>OsOm</sub>) (1 + Perd) + FE + K] + PA + CA")}</b></p>
<p>${_(u"On:")}</p>
<ul>
    <li>${_(u"<b>PH</b> = Preu horari de l’energia")}</li>
    <li>${_("<b>PHM</b> = Preu horari del mercat diari. Per als contractes de la península és el preu OMIE, mentre que a les illes Balears i Canàries és el preu horari de la demanda del sistema balear i canari respectivament.")}</li>
    <li>${_("<b>PHMA</b> = Preu horari del Mecanisme d’Ajust als costos de producció d’electricitat mitjançant el gas.")}</li>
    <li>${_("<b>Pc</b> = Pagaments per Capacitat definits pel Ministeri corresponent.")}</li>
    <li>${_("<b>SobrecostosREE</b> = sobrecostos publicats per REE per la gestió de la xarxa.")}</li>
    <li>${_("<b>Interrump</b> = Cost del servei d’Interrumpibilitat.")}</li>
    <li>${_("<b>P<sub>OsOm</sub></b> = Cost de l’Operador del sistema (REE) i de l’Operador del Mercat (OMIE). (El cost de l’Operador del Mercat (OMIE) no aplica a contractes de Balears i Canàries)")}</li>
    <li>${_("<b>Perd</b> = Pèrdues regulades de sistema des del punt de generació al punt de consum.")}</li>
    <li>${_("<b>FE</b> = Aportació al Fons d’Eficiència Energètica.")}</li>
    <li>${_("<b>K</b> = Marge de comercialització (que inclou els costos de desviament).")}</li>
    <li>${_("<b>PA</b> = Peatges de transport i distribució definits per la CNMC.")}</li>
    <li>${_("<b>CA</b> = Càrrecs del sistema definits pel Ministeri corresponent.")}</li>
</ul>
<p>${_(u"El marge de comercialització inclòs els costos de desviament pel punt de subministrament resulta:")}</p>
<p class="center">${_(u"<b>%s Euros/MWh</b>" % d.k_plus_D)}</p>
<p>${_(u"En cas de procedir a la contractació, aquest marge es podrà revisar anualment en funció del volum total d’energia utilitzada. Podeu ampliar la informació de la <b>tarifa indexada</b> en aquest <a href=\"%s\">document</a>.") % d.link}</p>
