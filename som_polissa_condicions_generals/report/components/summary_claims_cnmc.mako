<%def name="summary_claims_cnmc(cnmc, is_indexed)">
<%
    generation_link = "https://www.somenergia.coop/ca/tarifes-d-electricitat/" if cnmc.get('lang') == 'ca_es' else "https://www.somenergia.coop/es/tarifas-de-electricidad/"
    first_number = 10 if is_indexed else 9
    second_number = 11 if is_indexed else 10
%>
<div class="summary-box">
    <h3>${_(u"{}. Vies alternatives de reclamació disponibles per a la consumidora o el consumidor").format(first_number)}</h3>
    <div class="summary-content">
        <p class="section-text">${_(u"SOM ENERGIA, SCCL, està adherida a la Junta Arbitral Nacional de Consum i a les Juntes Arbitrals Autonòmiques.")}</p>
        <p class="section-text">${_(u"Junta Arbitral Nacional de Consum · Carrer Príncipe de Vergara, 54 · 28006 Madrid · junta-nacional@consumo.gob.es")}</p>
        <p class="section-text"><a href="https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo">https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo</a></p>
        <p class="section-text"><a href="https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo/organos/juntasArbitrales/autonomica">https://www.dsca.gob.es/es/consumo/como-reclamar-conflicto-consumo/sistema-arbitral-consumo/organos/juntasArbitrales/autonomica</a></p>
    </div>
</div>

<div class="summary-box">
    <h3>${_(u"{}. Accés al comparador d'ofertes de la CNMC").format(second_number)}</h3>
    <div class="summary-content">
        % if cnmc.get('is_visible'):
            <table class="summary-cnmc-table">
                <tr>
                    <td class="summary-cnmc-text">
                        <p class="section-text">${_(u"Amb aquest enllaç")} <a href="${cnmc.get('link_qr')}">comparador.cnmc.gob.es</a> ${_(u"pots consultar i comparar les diferents ofertes vigents de les comercialitzadores d'electricitat del mercat lliure.")}</p>
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
