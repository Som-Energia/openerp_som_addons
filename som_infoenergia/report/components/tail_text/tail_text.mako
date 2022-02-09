<%page args="d" />
<h3>${_(u"Permanència")}</h3>
<p>${_(u"En aquesta tarifa no s’aplica cap mena de permanència. Tot i això, en el moment en què es vulgui donar de baixa el subministrament amb la comercialitzadora caldrà fer-ho amb un preavís de trenta (30) dies d’antelació.")}</p>
<h3>${_(u"Vigència oferta")}</h3>
<p>${_(u"Aquesta oferta té una vigència de 15 dies naturals a partir de la data d’oferta.")}</p>
<h3>${_(u"Garantia per impagament")}</h3>
<p>${_(u"La contractació amb tarifa indexada està supeditada al pagament d’una <b>garantia en forma de dipòsit bancari executable en cas d’impagament.</b>")}</p>
<p>${_(u"Aquest dipòsit de garantia està calculat a partir de l’ús d’energia fet servir l’últim any, aplicant la nostra predicció de preu indexat de l'electricitat dels mesos vinents (no preu fix com fins ara), sense els descomptes provisionals que actualment està aplicant l’Estat als impostos i sense el descompte en els càrrecs que es van aplicar fins al desembre. Així, l’import del dipòsit és <b>%s €</b>." % d.import_garantia)}</p>
<p>${_(u"Aquest import és la nostra estimació del que podria arribar a representar una factura teva els pròxims mesos, en el cas que el preu de l'electricitat es mantingui elevat durant cada hora del dia.")}</p>
<p>${_(u"El pagament s’haurà de fer efectiu al compte bancari de Som Energia dins dels 7 dies posteriors a la signatura del contracte i en tot cas, abans del <b>%s</b>" % d.data_limit_ingres)}</p>