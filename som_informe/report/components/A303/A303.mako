<%page args="d" />
<li>
    ${_(u"El %s ens arriba una comunicació per part de la distribuïdora (%s) en relació a l’alta de subministrament amb codi de sol·licitud [%s]:") % (d.day, d.distribuidora, d.codi_solicitud) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> A3 (Alta de subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 03")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Data d'incidència:</b> %s") % (d.data_incidencia)}<br/>
    ${_(u"<b>Data prevista acció:</b> %s") % (d.data_prevista_accio)}<br/>
    % for incidencia in d.incidencies:
        ${_(u"<b>Tipus d'incidència:</b> %s") % (incidencia['tipus'])}<br/>
        ${_(u"<b>Comentaris sobre la incidència:</b> %s") % (incidencia['comentari'])}<br/>
        <br/>
    % endfor
    <br><br>
</li>