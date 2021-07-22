<%page args="d" />
<li>
    ${_(u"El %s ens arriba una comunicació per part de la distribuïdora ( %s ) en relació a la reclamació amb codi %s :") % (d.day, d.distribuidora, d.codi_reclamacio_distri) }<br/>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 03")}<br/>
    ${_(u"Data creació: %s") % (d.date)}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_sollicitud)}<br/>
    ${_(u"Codi de reclamació de la distribuïdora: %s ") % (d.codi_reclamacio_distri)}<br/>

    % if d.hi_ha_info_intermitja:
        ${_(u"Tipus de la Comunicació: %s ") % (d.desc_info_intermitja)}<br/>
    % elif d.hi_ha_retipificacio:
        ${_("Tipologia a la que es retipifica: %s") % (d.tipologia_retifica)}</br>
        ${_(u"Tipus de la Comunicació: %s ") % (d.desc_info_intermitja)}<br/>
    % elif d.hi_ha_sol_info_retip:
        ${_(u"Tipus de la Comunicació: %s ") % (d.desc_info_intermitja)}<br/>
    % elif hi_ha_solicitud:

    % else

    % endif

    % if len(d.documents_adjunts) > 0:
        ${_(u"Documents adjunts: Si")}<br/>
        ${_(u"Tipus de document: %s ") % (d.documents_adjunts)}<br/>
    % else:
        ${_(u"Documents adjunts: No")}<br/>
    % endif
    ${_(u"Comentari distribuïdora: %s ") % (d.comentaris_distri)}<br/>
</li>
