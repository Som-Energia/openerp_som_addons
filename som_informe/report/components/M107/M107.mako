<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens dóna l’acceptació/rebuig de la petició d’anul·lació tramitada:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> M1 (Alta de subministrament)")}<br/>
    ${_(u"<b>Pas:</b> 07")}<br/>
    ${_(u"<b>Data creacio:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Acceptació o Rebuig per part de la distribuidora:</b>")}
    % if d.rebuig:
        ${_(u"Rebuig")}<br/>
    % else:
        ${_(u"Acceptació")}<br/>
    % endif
    % for rebuig in d.rebutjos:
        ${_(u"<b>Descripció del Rebuig:</b> %s") % (rebuig['descripcio'])}<br/>
    % endfor
    <br><br>
</li>
