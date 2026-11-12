<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens comunica la incidència següent:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1")}<br/>
    ${_(u"<b>Pas:</b> 03")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    % for incidencia in d.incidencies:
        ${_(u"<b>Tipus d'incidència:</b> %s") % (incidencia['tipus'])}<br/>
        ${_(u"<b>Comentaris sobre la incidència:</b> %s") % (incidencia['comentari'])}<br/>
        <br/>
    % endfor
    ${_(u"<b>Data de la incidència:</b> %s") % (d.data_incidencia)}<br/>
    ${_(u"<b>Data prevista acció:</b> %s") % (d.data_prevista_accio)}<br/>
    <br><br>
</li>
