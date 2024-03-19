<%page args="d" />
<li>
    ${_("El [%s] Som Energia sol·licita l'anul·lació de la modificació contractual en curs amb codi de sol·licitud %s a la distribuïdora (%s):") % (d.create, d.codi_solicitud, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> M1 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 06")}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
