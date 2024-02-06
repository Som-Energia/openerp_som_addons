<%page args="d" />
<li>
    ${_(u"El %s Som Energia sol·licita l'anul·lació del canvi de comercialitzadora amb canvis en curs amb codi de sol·licitud %s a la distribuïdora (%s):") % (d.day, d.codi_solicitud , d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C2 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 08")}<br/>
    ${_(u"<b>Data creació -completa-:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
