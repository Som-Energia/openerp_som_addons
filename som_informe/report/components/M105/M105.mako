<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens dóna l’activació del cas tramitat:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> M1 (Modificació contractual)")}<br/>
    ${_(u"<b>Pas:</b> 05")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>

    %if d.tipus_sol == 'N' or d.tipus_sol=='A':
        ${_(u"<b>Tipus autoconsum:</b> %s") % (d.tipus_autoconsum)}<br/>
        %if d.control_potencia:
            ${_(u"<b>Control de potència:</b> %s")% (d.control_potencia)}<br/>
        %endif
        ${_(u"<b>Potència: </b>")}
        % for pot in d.potencies[:-1]:
            ${pot['name']} : ${pot['potencia']},
        % endfor
        ${d.potencies[-1]['name']}: ${d.potencies[-1]['potencia']}<br/>
        ${_(u"<b>Tarifa:</b> %s") % (d.tarifa)}<br/>
        %if d.tensio_sol:
            ${_(u"<b>Tensió sol·licitada:</b> %s")% (d.tensio_sol)}<br/>
        %endif
    %endif

    ${_(u"<b>Data activació:</b> %s")% (d.data_activacio)}<br/>
    <br><br>
</li>
