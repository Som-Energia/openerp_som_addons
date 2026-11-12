<%page args="d" />
<li>
    ${_(u"El %s sol·licitem l’anul·lació de la baixa de subministrament a la (%s)") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> B1 (Baixa de subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 03")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
