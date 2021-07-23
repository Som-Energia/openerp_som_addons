<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta una reclamació a la distribuïdora ( %s ):") % (d.day, d.distribuidora) }<br/>
    <br/>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 02")}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_solicitud)}<br/>
    ${_(u"Data creació: %s") % (d.create)}<br/>
    % if d.rebuig:
        ${_(u"Acceptació o rebuig per part de la distribuïdor: Rebuig ")}<br/>
        ${_(u"Descripció del Rebuig: %s ") % (d.motiu_rebuig)}<br/> 
    % else:
        ${_(u"Acceptació o rebuig per part de la distribuïdor: Acceptació ")}<br/>
    % endif
    ${_(u"Codi de reclamació de la distribuïdora: %s ") % (d.codi_reclamacio_distri)}<br/>
    % if d.rebuig:
        ${_(u"Data de rebuig: %s ") % (d.data_rebuig)}<br/>
    % else:
        ${_(u"Data d’acceptació: %s ") % (d.data_acceptacio)}<br/>
    % endif

    <br/>
</li>
