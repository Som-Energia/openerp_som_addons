<%page args="d" />
<li>
    ${_(u"El %s aportem informació addicional a la distribuïdora ( %s ) en relació a la reclamació amb codi %s:") % (d.day, d.distribuidora, d.codi_reclamacio_distri) }<br/>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 04")}<br/>
    ${_(u"Data creació: %s") % (d.date)}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_sollicitud)}<br/>
    ${_(u"Tipus:") % (d.tipus)}<br/>
    ${_(u"Codi de reclamació de la distribuïdora: %s ") % (d.codi_reclamacio_distri)}<br/>
    % if len(d.documents_adjunts) > 0:
        ${_(u"Documents adjunts: Si")}<br/>
        ${_(u"Tipus de document: %s ") % (d.documents_adjunts)}<br/>
    % else:
        ${_(u"Documents adjunts: No")}<br/>
    % endif
    ${_(u"Comentari: %s ") % (d.comentaris_distri)}<br/>
</li>
