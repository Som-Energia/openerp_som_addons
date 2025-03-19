<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens dóna l’activació del desistiment tramitat per Som Energia:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1")}<br/>
    ${_(u"<b>Pas:</b> 05")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data d'activació:</b> %s") % (d.data_activacio)}<br/>
    ${_(u"<b>Resultat activació:</b> %s") % (d.resultat_activacio)}<br/>
    <br><br>
</li>
