<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens comunica l’acceptació d’una sol·licitud d'anul·lació de la sol·licitud de canvi que ha enviat anteriorment. Per tant, ens indica que finalment el contracte no farà canvi de companyia i seguirà a Som Energia:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> C2 (Canvi de Comercialitzadora sense modificacions en el contracte d’accés)")}<br/>
    ${_(u"<b>Pas:</b> 10")}<br/>
    ${_(u"<b>Data creació -completa-:</b> %s") % (d.create)}<br/>
    ${_(u"<b>Data d'acceptació:</b> %s") % (d.data_acceptacio)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    <br><br>
</li>
