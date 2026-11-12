<%page args="d" />
<li>
    ${_(u"El %s Som Energia sol·licita l'anul·lació de l’alta en curs amb codi de sol·licitud %s a la distribuïdora (%s):") % (d.day, d.codi_solicitud, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> A3 (Alta de subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 06")}<br/>
    ${_(u"<b>Data creacio:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
