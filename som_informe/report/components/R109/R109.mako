<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora ( %s ) ens dóna l’acceptació/rebuig de la petició d’anul·lació tramitada:") % (d.date, d.distribuidora) }<br/>
    <br/>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 09")}<br/>
    ${_(u"Data creació: %s") % (d.date)}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_solicitud)}<br/>
    % if d.rebuig:
        ${_(u"Acceptació o rebuig per part de la distribuïdor: Rebuig")}<br/>
        ${_(u"Descripció del Rebuig: %s ") % (d.motiu_rebuig)}<br/> 
    % else:
        ${_(u"Acceptació o rebuig per part de la distribuïdor: Acceptació")}<br/>
    % endif
    <br/>
</li>
