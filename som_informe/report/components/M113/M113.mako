<%page args="d" />
<li>
    ${_(u"El %s Som Energia aporta una informació addicional a la distribuïdora ( %s ) en relació amb la modificació en curs:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b>  M1 (Modificació contractual)")}<br/>
    ${_(u"<b>Pas:</b> 13")}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.data_creacio)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Contestació incidència:</b> %s") % (d.contestacio_incidencia)}<br/>
    ${_(u"<b>Nom de Contacte:</b> %s") % (d.nom_contacte)}<br/>
    ${_(u"<b>Telèfons: </b>")}
    % for telefon in d.telefons:
        ${_(u"%s ") % (telefon['numero'])}
    % endfor
    <br/>
    ${_(u"<b>E-mail de Contacte:</b> %s") % (d.email_contacte)}<br/>
    <br/>
</li>