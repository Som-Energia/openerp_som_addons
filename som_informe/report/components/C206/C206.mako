<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens comunica que el contracte causa baixa per canvi de companyia comercialitzadora amb canvis en el contracte d’accés:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C2 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 06")}<br/>
    ${_(u"<b>Data d'activacio del canvi:</b> %s") % (d.data_activacio)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br/>
</li>

