<%def name="summary_claims_cnmc(cnmc)">
<%
    generation_link = "https://www.somenergia.coop/ca/tarifes-d-electricitat/" if cnmc.get('lang') == 'ca_es' else "https://www.somenergia.coop/es/tarifas-de-electricidad/"
%>
<div class="summary-box">
    <h3>10. Vías alternativas de reclamación disponibles al consumidor</h3>
    <div class="summary-content">
        <p class="section-text">SOM ENERGIA está adherida a la Junta Arbitral Nacional de Consumo y a las Juntas Arbitrales Autonómicas.</p>
        <p class="section-text">Junta Arbitral Nacional de Consumo · Calle Príncipe de Vergara, 54 · 28006 Madrid · junta-nacional@consumo.gob.es</p>
        <p class="section-text"><a href="https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo">https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo</a></p>
        <p class="section-text"><a href="https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo/organos/juntasArbitrales/autonomica">https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo/organos/juntasArbitrales/autonomica</a></p>
    </div>
</div>

<div class="summary-box">
    <h3>11. Acceso al comparador de ofertas de la CNMC</h3>
    <div class="summary-content">
        % if cnmc.get('is_visible'):
            <table class="summary-cnmc-table">
                <tr>
                    <td class="summary-cnmc-text">
                        <p class="section-text">Con este enlace <a href="${cnmc.get('link_qr')}">comparador.cnmc.gob.es</a> puedes consultar y comparar las diferentes ofertas vigentes de las comercializadoras de electricidad del mercado libre.</p>
                    </td>
                    <td class="summary-cnmc-qr">
                        % if cnmc.get('qr_image'):
                            <img class="summary-cnmc-qr-image" src="${'data:image/png;base64, {}'.format(cnmc.get('qr_image'))}">
                        % else:
                            <img class="summary-cnmc-qr-image" src="${addons_path}/giscedata_facturacio_comer_som/report/components/cnmc_comparator_qr_link/generic_qr_comparator.png">
                        % endif
                    </td>
                </tr>
            </table>
        % endif
    </div>
</div>
</%def>
