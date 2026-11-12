<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta la sol·licitud següent a la distribuïdora (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1 (Desistiment)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Tipus sol·licitud:</b> %s") % (d.tipus_solicitud)}<br/>
    ${_(u"<b>Cas ATR subjacent:</b>")}<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;${_(u"Codi sol·licitud: %s") % (d.codi_subjacent)}<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;${_(u"Data sol·licitud: %s") % (d.data_subjacent)}<br/>
    <br><br>
</li>
