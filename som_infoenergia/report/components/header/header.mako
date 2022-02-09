<%page args="d" />
<p>${_(u'%s') % d.data_oferta}</p>
<p>${_(u'%s') % d.codi_oferta}</p>
<div style="background-color: green; display: flex; justify-content: space-between;">
    <p style="color: white;">${_(u'%s') % d.nom_titular}</p>
    <p style="color: white;">${_(u'%s') % d.data_oferta}</p>
</div>