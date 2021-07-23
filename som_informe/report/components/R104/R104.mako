<%page args="d" />
<li>
    ${_(u"El %s aportem informació addicional a la distribuïdora ( %s ) :") % (d.day, d.distribuidora) }<br/>
    <br/>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 04")}<br/>
    ${_(u"Data creació: %s") % (d.date)}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_solicitud)}<br/>
    <%
        tipus = []
        if d.hi_ha_client:
            tipus.append(_("client"))
        if d.hi_ha_var_info:
            tipus.append(_("variables aportacio informacio"))
        if d.hi_ha_var_info_retip:
            tipus.append(_("variables aportacio informacio per retipificacio"))
    %>
    % if tipus:
        ${_(u"Tipus: %s") % (",".join(tipus))}<br/>
    % endif
    % if len(d.documents_adjunts) > 0:
        ${_(u"Documents adjunts: Si")}<br/>
        ${_(u"Tipus de document:")}<br/>
        % for doc in d.documents_adjunts:
             ${_(' - %s, <a href="%s">enllaç al document</a>') % (doc[0], doc[1])}<br/>
        % endfor
    % else:
        ${_(u"Documents adjunts: No")}<br/>
    % endif
    ${_(u"Comentari: %s ") % (d.comentaris_distri)}<br/>
    <br/>
</li>
