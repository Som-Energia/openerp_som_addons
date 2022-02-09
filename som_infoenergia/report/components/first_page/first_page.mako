<%page args="d" />
<style>
<%include file="first_page.css" />
</style>
<div class="logo" style="margin-bottom: 15px; ">
    <img src="${addons_path}/som_infoenergia/report/components/first_page/logo_som.png"/>
</div>
<h1 style="font-weight: bold;">${_(u'Oferta tarifa indexada Som Energia')}</h1>
<h2 style="font-weight: bold;">${_(u'%s') % d.nom_titular}</h2>