<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta la sol·licitud següent a la distribuïdora (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C1 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    % if d.text:
        ${_(u"<b>Comentaris:</b> <i>%s</i>") % (d.text)}<br/>
    % endif
    ${_(u"<b>Documents adjunts: </b>")}
    % if d.adjunts:
        ${_(u"Sí")}<br/>
    % else:
        ${_(u"No")}<br/>
    % endif
    <br><br>
</li>
