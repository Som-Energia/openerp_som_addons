<%page args="d" />
<%
    setLang(d.lang)
%>
<div class="logo">
    <img src="${addons_path}/som_infoenergia/report/components/first_page/logo_som.png"/>
</div>
<h1>${_(u'Oferta tarifa indexada Som Energia')}</h1>
<h2>${_(u'%s') % d.nom_titular}</h2>
<p class="data-oferta">${_(u'%s') % d.data_oferta}</p>
<p class="codi-oferta">${_(u'%s') % d.codi_oferta}</p>
