<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens informa de l’activació del cas sol·licitat per Som Energia:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b>  B1 (Baixa de subministrament o suspensió del subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 05")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data activació:</b> %s") % (d.data_activacio)}<br/>
    <br><br>
</li>
