 <%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta la sol·licitud següent a la distribuïdora (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C2 (Canvi de Comercialitzadora amb modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Tipologia de la sol·licitud:</b> %s") % (d.tipologia_solicitud)}<br/>
    ${_(u"<b>Canvi de titular:</b> %s") % (d.canvi_titular)}<br/>
    ${_(u"<b>Nom de la persona o societat:</b> %s") % (d.nom)}<br/>
    ${_(u"<b>Primer cognom:</b> %s") % (d.primer_cognom)}<br/>
    ${_(u"<b>Segon cognom:</b> %s") % (d.segon_cognom)}<br/>
    ${_(u"<b>Document acreditatiu:</b> %s") % (d.document_acreditatiu)}<br/>
    ${_(u"<b>Codi document:</b> %s") % (d.codi_document)}<br/>
    %if d.tipologia_solicitud == 'A' or d.tipologia_solicitud == 'N':
        ${_(u"<b>Tipus de contracte:</b> %s") % (d.tipus_contracte)}<br/>
        ${_(u"<b>Tipus autoconsum:</b> %s") % (d.tipus_autoconsum)}<br/>
        %if d.control_potencia:
            ${_(u"<b>Control de potència:</b> %s")% (d.control_potencia)}<br/>
        % endif
        ${_(u"<b>Potència: </b>")}
        % for pot in d.potencies[:-1]:
            ${pot['name']} : ${pot['potencia']},
        % endfor
        ${d.potencies[-1]['name']}: ${d.potencies[-1]['potencia']} <br/>
        ${_(u"<b>Tarifa:</b> %s") % (d.tarifa)}<br/>
        %if d.tensio:
            ${_(u"<b>Tensió:</b> %s") % (d.tensio)}<br/>
        %endif
        ${_(u"<b>Comentaris:</b> %s") % (d.comentaris)}<br/>
        %if d.adjunts:
            ${_(u"<b>Documentació adjunta:</b> Sí")}<br/>
        %else:
            ${_(u"<b>Documentació adjunta:</b> No")}<br/>
        %endif
    %endif
    <br><br>
</li>
