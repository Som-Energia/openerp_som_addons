<%page args="d" />
<li>
    ${_(u"El %s Som Energia, atenent al que ens indica la persona titular, presenta a  la distribuïdora (%s) la següent resposta d’acceptació o rebuig a la informació del D1 01:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> D1 (Autoconsum)")}<br/>
    ${_(u"<b>Pas:</b> 02")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Acceptació o Rebuig:</b>")}
    % if d.rebuig:
        ${_(u"Rebuig")}<br/>
        % for rebuig in d.rebutjos:
            ${_(u"<b>Codi Motiu de Rebuig:</b> %s") % (rebuig['codi'])}<br/>
            ${_(u"<b>Descripció del Rebuig:</b> %s") % (rebuig['descripcio'])}<br/>
        % endfor
    % else:
        ${_(u"Acceptació")}<br/>
    % endif
    <br><br>
</li>
