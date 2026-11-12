<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta la sol·licitud següent a la distribuïdora (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> B2 (Baixa de subministrament o suspensió del subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 05")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Motiu de la baixa:</b> %s") % (d.motiu_baixa)}<br/>
    ${_(u"<b>Data d'activació:</b> %s") % (d.data_activacio)}<br/>
    <br><br>
</li>
