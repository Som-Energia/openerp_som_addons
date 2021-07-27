<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta una reclamació a la distribuïdora ( %s ):") % (d.day, d.distribuidora) }<br/>
    <br/>
    ${_(u"<b>Procediment:</b> R1 (reclamació)")}<br/>
    ${_(u"<b>Pas:</b> 05")}<br/>
    ${_(u"<b>Data tancament de la reclamació:</b> %s") % (d.date)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Codi de reclamació de la distribuïdora:</b> %s ") % (d.codi_reclamacio_distri)}<br/>
    ${_(u"<b>Resultat de la reclamació:</b> %s ") % (d.resultat)}<br/>
    % if d.detall_resultat:
        ${_(u"<b>Detall Resultat reclamació:</b> %s ") % (d.detall_resultat)}<br/>
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
    ${_(u"<b>Argumentació per part de la distribuïdora:</b> %s ") % (d.comentaris_distri)}<br/>
    <br/>
</li>
