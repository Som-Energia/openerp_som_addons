<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta una reclamació a la distribuïdora (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> R1 (reclamació)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Tipus de reclamació:</b> %s") %(d.tipus_reclamacio)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    % if len(d.variables_aportacio):
        ${_(u"<b>Variables d'aportació:</b> %s variable(s)") % (str(len(d.variables_aportacio)))}<br/>
        % for var_apo in d.variables_aportacio:
            % if var_apo['descripcio']:
                ${_(' - <b>%s:</b> %s  tipus: <i>%s</i>  descripció: <i>%s</i>') % (var_apo['variable'], var_apo['valor'], var_apo['tipus'], var_apo['descripcio'])}<br/>
            % else:
                ${_(' - <b>%s:</b> %s  tipus: <i>%s</i>') % (var_apo['variable'], var_apo['valor'], var_apo['tipus'])}<br/>
            % endif
        % endfor
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
    ${_(u"<b>Text de la reclamació:</b> <i>%s</i>") % (d.text)}<br/>
    <br><br>
</li>

