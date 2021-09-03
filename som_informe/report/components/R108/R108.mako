<%page args="d" />
<li>
    ${_(u"El %s Som Energia sol·licita l'anul·lació de la reclamació en curs amb codi de sol·licitud %s a la distribuïdora (%s):") % (d.date, d.codi_reclamacio_distri, d.distribuidora) }<br/>
    <br/>
    ${_(u"<b>Procediment:</b> R1 (reclamació)")}<br/>
    ${_(u"<b>Pas:</b> 08")}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Codi de reclamació de la distribuïdora:</b> %s") % (d.codi_reclamacio_distri)}<br/>
    <br><br>
</li>
