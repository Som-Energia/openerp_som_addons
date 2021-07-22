<%page args="d" />
<li>
    ${_(u"El %s Som Energia sol·licita l'anul·lació de la reclamació en curs amb codi de sol·licitud %s a la distribuïdora ( %s ):") % (d.date, d.codi_sollicitud, d.distribuidora) }<br/>
    ${_(u"Procediment: R1 (reclamació)")}<br/>
    ${_(u"Pas: 08")}<br/>
    ${_(u"Data creació: %s") % (d.date)}<br/>
    ${_(u"Codi de la sol·licitud: %s") % (d.codi_sollicitud)}<br/>
    ${_(u"Codi de reclamació de la distribuïdora: %s ") % (d.codi_reclamacio_distri)}<br/>
    ${_(u"Tipus de reclamació: %s") %(d.tipus_reclamacio)}<br/>
</li>
