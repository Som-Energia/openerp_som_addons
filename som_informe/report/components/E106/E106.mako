<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens notifica l’acceptació d’un desistiment com a comercialitzadora sortint:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> E1")}<br/>
    ${_(u"<b>Pas:</b> 06")}<br/>
    ${_(u"<b>Data d'activació':</b> %s") % (d.data_alta)}<br/>
    <br><br>
</li>