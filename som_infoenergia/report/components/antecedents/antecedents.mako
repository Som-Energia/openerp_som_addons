<%page args="d" />
<h2>${_(u'Antecedents')}</h2>
<p>${_(u'<strong>%s</strong> disposa del contracte de subministrament elèctric de <strong>%s</strong>, amb CUPS <strong>%s</strong> i per això vol obtenir la millor oferta de <strong>preu indexat</strong> que Som Energia pugui oferir com a comercialitzadora.<br/><br/>El volum total d’energia és d’aproximadament <strong>%s</strong> kWh anuals.' % (d.nom_titular, d.direccio, d.cups, d.consum_anual))}</p>
