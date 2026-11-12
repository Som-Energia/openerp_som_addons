<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens dóna l’acceptació/rebuig de l’anul·lació sol·licitada com a comercialitzadora entrant o en vigor:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1")}<br/>
    ${_(u"<b>Pas:</b> 09")}<br/>
    ${_(u"<b>Codi de sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data d'acceptació/rebuig:</b> %s") % (d.data_rebuig)}<br/>
    <br><br>
</li>
