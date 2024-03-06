<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s)  ens comunica el rebuig del desistiment enviat per Som Energia:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1")}<br/>
    ${_(u"<b>Pas:</b> 04")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data Rebuig:</b> %s") % (d.data_rebuig)}<br/>
    <br><br>
</li>
