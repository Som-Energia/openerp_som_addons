<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens informa sobre l’acceptació/rebuig de l’anul·lació sol·licitada:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> B1")}<br/>
    ${_(u"<b>Pas:</b> 04")}<br/>
    ${_(u"<b>Codi de sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data d'acceptació/rebuig:</b> %s") % (d.data_rebuig)}<br/>
    <br><br>
</li>
