<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora ( %s ) ens dóna l’acceptació/rebuig de la petició d’anul·lació tramitada:") % (d.date, d.distribuidora) }<br/>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 09")}<br/>
    ${_(u"Data creació: %s") % (d.date)}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_sollicitud)}<br/>
    ${_(u"Codi de reclamació de la distribuïdora: %s ") % (d.codi_reclamacio_distri)}<br/>
    ${_(u"Tipus de reclamació: %s") %(d.tipus_reclamacio)}<br/>
    % if d.rebuig:
        ${_(u"Acceptació o rebuig per part de la distribuïdor: Rebuig")}<br/>
        ${_(u"Descripció del Rebuig: %s ") % (d.motiu_rebuig)}<br/> 
    % else:
        ${_(u"Acceptació o rebuig per part de la distribuïdor: Acceptació")}<br/>
    % endif
</li>
