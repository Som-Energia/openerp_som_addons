 <%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens comunica el rebuig en camp de la sol·licitud de canvi que ha enviat anteriorment. Per tant, ens indica que finalment el contracte no farà canvi de companyia i seguirà a Som Energia:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C1 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 12")}<br/>
    ${_(u"<b>Data creació -completa-:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Data de rebuig:</b> %s") % (d.data_rebuig)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
