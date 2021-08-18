<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora ( %s ) ens comunica el rebuig en camp de l’alta de subministrament amb codi de sol·licitud [%s]:") % (d.day, d.distribuidora, d.codi_solicitud) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> B1 (Baixa de subministrament o suspensió del subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 07")}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data Rebuig:</b> %s") % (d.data_rebuig)}<br/>
    % for rebuig in d.rebuigs:
        ${_(u"<b>Motiu:</b> %s") % (rebuig['codi_rebuig'])}<br/>
        ${_(u"<b>Descripció:</b> %s") % (rebuig['comentari'])}<br/>
        <br/>
    % endfor
</li>