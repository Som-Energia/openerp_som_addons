<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens informa de l’acceptació de l’anul·lació sol·licitada, com a comercialitzadora sortint:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1 (Desistiment)")}<br/>
    ${_(u"<b>Pas:</b> 10")}<br/>
    ${_(u"<b>Data d'acceptació:</b> %s") % (d.data_acceptacio)}<br/>
    <br><br>
</li>
