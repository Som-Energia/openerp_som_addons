<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta la sol·licitud següent a la distribuïdora (%s)") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> M1 (Modificació contractual)")}<br/>
    ${_(u"<b>Pas:</b> 05")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>

    %if d.tipus_sol == 'N' or d.tipus_sol=='A':
        ${_(u"<b>Tipus autoconsum:</b> %s") % (d.tipus_autoconsum)}<br/>
        ${_(u"<b>Control de potència:</b> %s")% (d.control_potencia)}<br/>
        ${_(u"<b>Potència: </b>")}
        % for pot in d.potencies[:-1]:
            ${pot['name']} : ${pot['potencia']},
        % endfor
        ${d.potencies[-1]['name']}: ${d.potencies[-1]['potencia']}<br/>
        ${_(u"<b>Tarifa:</b> %s") % (d.tarifa)}<br/>
        ${_(u"<b>Tensió sol·licitada:</b> %s")% (d.tensio_sol)}<br/>
    %endif

    ${_(u"<b>Data activació:</b> %s")% (d.data_activacio)}<br/>
    <br><br>
</li>