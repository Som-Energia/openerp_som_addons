<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens dóna l’acceptació/rebuig de la petició d’anul·lació tramitada:") % (d.date, d.distribuidora) }<br/>
    <br/>
    ${_(u"<b>Procediment:</b> R1 (reclamació)")}<br/>
    ${_(u"<b>Pas:</b> 09")}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Codi de reclamació de la distribuïdora:</b> %s") % (d.codi_reclamacio_distri)}<br/>
    % if d.rebuig:
        ${_(u"<b>Acceptació o rebuig per part de la distribuïdor:</b> Rebuig")}<br/>
        ${_(u"<b>Descripció del Rebuig:</b> %s ") % (d.motiu_rebuig)}<br/>
    % else:
        ${_(u"<b>Acceptació o rebuig per part de la distribuïdor:</b> Acceptació")}<br/>
    % endif
    <br><br>
</li>
