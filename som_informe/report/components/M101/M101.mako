<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta la sol·licitud següent a la distribuïdora (%s)") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> M1 (Modificació contractual)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>

    %if d.tipus_sol == 'A' or d.tipus_sol=='S':
        ${_(u"<b>Canvi de titular:</b> %s") % (d.canvi_titular)}<br/>
        ${_(u"<b>Nom de la persona o societat:</b> %s") % (d.nom)}<br/>
        ${_(u"<b>Primer cognom:</b> %s") % (d.cognom1)}<br/>
        ${_(u"<b>Segon cognom:</b> %s") % (d.cognom2)}<br/>
        ${_(u"<b>Document identificatiu:</b> %s") % (d.document_identificatiu)}<br/>
        ${_(u"<b>Codi document:</b> %s") % (d.codi_document)}<br/>
    %endif

    %if d.tipus_sol == 'N' or d.tipus_sol=='A':
        ${_(u"<b>Tipus autoconsum:</b> %s") % (d.tipus_autoconsum)}<br/>
        %if d.control_potencia:
            ${_(u"<b>Control de potència:</b> %s")% (d.control_potencia)}<br/>
        %endif
        ${_(u"<b>Solicitud Tensió:</b>")}
        %if d.sol_tensio == 'S':
            ${_(u"Sí")}<br/>
        %else:
            ${_(u"No")}<br/>
        %endif
        %if d.tensio_sol:
            ${_(u"<b>Tensió sol·licitada:</b> %s")% (d.tensio_sol)}<br/>
        %endif
        ${_(u"<b>Potència: </b>")}
        % for pot in d.potencies[:-1]:
            ${pot['name']} : ${pot['potencia']},
        % endfor
        ${d.potencies[-1]['name']}: ${d.potencies[-1]['potencia']}<br/>
        ${_(u"<b>Tarifa:</b> %s") % (d.tarifa)}<br/>
        ${_(u"<b>Telèfon de contacte: </b>")}
        % for pot in d.telefons[:-1]:
            ${pot['numero']},
        % endfor
        ${d.telefons[-1]['numero']}.
    %endif
    <br><br>
</li>
