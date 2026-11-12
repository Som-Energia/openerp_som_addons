<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens comunica el rebuig en camp del canvi de comercialitzadora amb codi de sol·licitud %s:") % (d.day, d.distribuidora, d.codi_solicitud) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C2 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 04")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data rebuig:</b> %s") % (d.data_rebuig)}<br/>
    % for rebuig in d.rebutjos:
        ${_(u"<b>Codi Motiu de Rebuig:</b> %s") % (rebuig['codi'])}<br/>
        ${_(u"<b>Descripció del Rebuig:</b> %s") % (rebuig['descripcio'])}<br/>
    % endfor
    <br><br>
</li>
