<%page args="d" />
<li>
    ${_(u"El %s sol·licitem l’anul·lació del desistiment com a comercialitzadora entrant o en vigor a la (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1 (Desistiment)")}<br/>
    ${_(u"<b>Pas:</b> 08")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
