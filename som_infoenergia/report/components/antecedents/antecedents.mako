<%page args="d" />
<h3>${_(u'Antecedents')}</h3>
<p>${_(u'<b>%s</b> disposa del contracte de subministrament elèctric de <b>%s</b>, amb CUPS <b>%s</b>  i per tal de renovar el contracte Som Energia presenta la millor oferta de <b>preu indexat</b> que pot oferir com a comercialitzadora.') % (d.nom_titular, d.direccio, d.cups)}</p>
<p>${_(u'El volum total d’energia és d’aproximadament <b>%s</b> kWh anuals.') % d.consum_anual}</p>
