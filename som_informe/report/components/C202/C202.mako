<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens dóna l'acceptació/rebuig del cas tramitat:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C2 (Canvi de Comercialitzadora amb modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 02")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Acceptació o Rebuig per part de la distribuïdora:</b>")}
    % if d.rebuig:
        ${_(u"Rebuig")}<br/>
        % for rebuig in d.rebutjos:
            ${_(u"<b>Codi Motiu de Rebuig:</b> %s") % (rebuig['codi'])}<br/>
            ${_(u"<b>Descripció del Rebuig:</b> %s") % (rebuig['descripcio'])}<br/>
        % endfor
        ${_(u"<b>Data rebuig:</b> %s") % (d.data_rebuig)}<br/>
    % else:
        ${_(u"Acceptació")}<br/>
    % endif
    <br><br>
</li>
