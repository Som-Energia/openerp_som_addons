<%def name="summary_claims_cnmc(is_indexed)">
<%
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
        <table class="summary-cnmc-table">
            <tr>
                <td class="summary-cnmc-text">
                    <p class="section-text">${_(u"Amb aquest enllaç")} <a href="https://comparador.cnmc.gob.es/">comparador.cnmc.gob.es</a> ${_(u"pots consultar i comparar les diferents ofertes vigents de les comercialitzadores d'electricitat del mercat lliure.")}</p>
                </td>
                <td class="summary-cnmc-qr">
                    <img class="summary-cnmc-qr-image" src="${addons_path}/som_polissa_condicions_generals/report/assets/generic_qr_comparator.png">
                </td>
            </tr>
        </table>
    </div>
</div>
</%def>
