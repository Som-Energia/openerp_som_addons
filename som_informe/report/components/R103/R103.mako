<%page args="d" />
<li>
    ${_(u"El %s ens arriba una comunicació per part de la distribuïdora (%s) en relació a la reclamació amb codi %s :") % (d.day, d.distribuidora, d.codi_reclamacio_distri) }<br/>
    <br/>
    ${_(u"<b>Procediment:</b> R1 (reclamació)")}<br/>
    ${_(u"<b>Pas:</b> 03")}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Codi de reclamació de la distribuïdora:</b> %s") % (d.codi_reclamacio_distri)}<br/>
    ${_(u"<b>Tipus de la Comunicació:</b> %s") % (d.tipus_comunicacio)}<br/>
    % if d.hi_ha_retipificacio:
        ${_(u"<b>Tipologia a la que es retipifica:</b> %s") % (d.tipologia_retifica)}<br/>
    % elif d.hi_ha_sol_info_retip:
        ${_(u"<b>Tipologia a la que es retipifica:</b> %s") % (d.tipologia_sol_retip)}<br/>
    % endif
    % if len(d.documents_adjunts) > 0:
        ${_(u"<b>Documents adjunts:</b> Si")}<br/>
        ${_(u"<b>Tipus de document:</b>")}<br/>
        % for doc in d.documents_adjunts:
             ${_(' - %s, <a href="%s">enllaç al document</a>') % (doc[0], doc[1])}<br/>
        % endfor
    % else:
        ${_(u"<b>Documents adjunts:</b> No")}<br/>
    % endif
    ${_(u"<b>Comentari distribuïdora:</b> <i>%s</i>") % (d.comentaris_distri)}<br/>
    <br><br>
</li>
