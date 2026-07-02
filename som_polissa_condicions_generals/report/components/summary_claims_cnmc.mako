<%def name="summary_claims_cnmc(cnmc)">
<%
    generation_link = "https://www.somenergia.coop/ca/tarifes-d-electricitat/" if cnmc.get('lang') == 'ca_es' else "https://www.somenergia.coop/es/tarifas-de-electricidad/"
%>
<div class="summary-box">
    <h3>1. Vías alternativas de reclamación disponibles al consumidor</h3>
    <div class="summary-content">
        <p class="section-text">SOM ENERGIA está adherida a la Junta Arbitral Nacional de Consumo y a las Juntas Arbitrales Autonómicas.</p>
        <p class="section-text">Junta Arbitral Nacional de Consumo · Calle Príncipe de Vergara, 54 · 28006 Madrid · junta-nacional@consumo.gob.es</p>
        <p class="section-text"><a href="https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo">https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo</a></p>
        <p class="section-text"><a href="https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo/organos/juntasArbitrales/autonomica">https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo/organos/juntasArbitrales/autonomica</a></p>
    </div>
</div>

<div class="summary-box">
    <h3>2. Acceso al comparador de ofertas de la CNMC</h3>
    <div class="summary-content">
        % if cnmc.get('is_visible'):
            <p class="section-text">Con este enlace <a href="${cnmc.get('link_qr')}">comparador.cnmc.gob.es</a> puedes consultar y comparar las diferentes ofertas vigentes de las comercializadoras de electricidad del mercado libre.</p>
        % endif
    </div>
</div>
</%def>
