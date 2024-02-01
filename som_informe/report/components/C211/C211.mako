<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens comunica l’acceptació d’una sol·licitud de canvi  de companyia amb canvis del contracte en curs. Per tant, ens indica que de forma imminent el contracte canviarà de companyia comercialitzadora amb algun o alguns canvis en el contracte d’accés:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C2 (Canvi de Comercialitzadora amb modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 11")}<br/>
    ${_(u"<b>Data creació -completa-:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Data de canvi o alta:</b> %s") % (d.data_activacio)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
