<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens dóna l’acceptació/rebuig de la petició d’anul·lació tramitada:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C1 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 08")}<br/>
    ${_(u"<b>Data creació -completa-:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
