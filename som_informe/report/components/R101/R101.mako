<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta una reclamació a la distribuïdora ( %s ):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 01")}<br/>
    ${_(u"Tipus de reclamació: %s") %(d.tipus_reclamacio)}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_solicitud)}<br/>
    ${_(u"Data creació: %s") % (d.create)}<br/>
    ${_(u"Text de la reclamació: %s ") % (d.text)}<br/>
    <br/>
</li>

