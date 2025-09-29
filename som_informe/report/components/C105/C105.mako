<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s)  ens dóna l’activació del cas tramitat:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C1 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 05")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Tipus contracte:</b> %s") % (d.tipus_contracte)}<br/>
    ${_(u"<b>Tipus Autoconsum:</b> %s") % (d.tipus_autoconsum)}<br/>
    ${_(u"<b>Codi contracte:</b> %s") % (d.codi_contracte)}<br/>
     ${_(u"<b>Potència: </b>")}
     % for pot in d.potencies[:-1]:
        ${pot['name']} : ${pot['potencia']},
    % endfor
    ${d.potencies[-1]['name']}: ${d.potencies[-1]['potencia']} <br/>
    ${_(u"<b>Tarifa:</b> %s") % (d.tarifa)}<br/>
    %if d.tensio:
        ${_(u"<b>Tensió:</b> %s") % (d.tensio)}<br/>
    %endif
    ${_(u"<b>Data activació:</b> %s") % (d.data_activacio)}<br/>
    <br><br>
</li>
