<%page args="d" />
<li>
    ${_(u"El %s aportem informació addicional a la distribuïdora ( %s ):") % (d.day, d.distribuidora) }<br/>
    <br/>
    ${_(u"<b>Procediment:</b> R1 (reclamació)")}<br/>
    ${_(u"<b>Pas:</b> 04")}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.date)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
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
        ${_(u"<b>Tipus:</b> %s") % (",".join(tipus))}<br/>
    % endif
    % if len(d.documents_adjunts) > 0:
        ${_(u"<b>Documents adjunts:</b> Si")}<br/>
        ${_(u"<b>Tipus de document:</b>")}<br/>
        % for doc in d.documents_adjunts:
             ${_(' - %s, <a href="%s">enllaç al document</a>') % (doc[0], doc[1])}<br/>
        % endfor
    % else:
        ${_(u"<b>Documents adjunts::</b> No")}<br/>
    % endif
    ${_(u"<b>Comentari:</b> <i>%s</i>") % (d.comentaris_distri)}<br/>
    <br/>
</li>
