<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta la sol·licitud següent a la distribuïdora (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> A3 (Alta de subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Tipus de contracte:</b> %s") %(d.tipus_contracte)}<br/>
    ${_(u"<b>Potència sol·licitada: </b>")}
    % for pot in d.potencies[:-1]:
        ${pot['name']} : ${pot['potencia']},
    % endfor
    ${d.potencies[-1]['name']}: ${d.potencies[-1]['potencia']}
    <br/>
    ${_(u"<b>Tarifa:</b> %s") % (d.tarifa)}<br/>
    % if d.text:
        ${_(u"<b>Comentaris:</b> <i>%s</i>") % (d.text)}<br/>
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
    <br><br>
</li>
