<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora ( %s )  ens comunica el rebuig de la baixa després d’actuacions en camp, per concórrer al mateix temps o bé un canvi de comercialitzadora vigent o bé una incidència en camp:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> B1")}<br/>
    ${_(u"<b>Pas:</b> 07")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data Rebuig:</b> %s") % (d.data_rebuig)}<br/>
    % for rebuig in d.rebuigs:
        ${_(u"<b>Motiu:</b> %s") % (rebuig['codi_rebuig'])}<br/>
        ${_(u"<b>Descripció:</b> %s") % (rebuig['comentari'])}<br/>
        <br/>
    % endfor
</li>