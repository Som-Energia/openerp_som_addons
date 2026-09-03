<%def name="cnmc_comparator_qr_link()">
    <div class="cnmc_qr_info">
        <h5>${_(u"COMPARADOR DE PREUS DE LA CNMC")}</h5>
        <div class="cnmc_qr_content">
            <div class="cnmc_qr_text">
                ${_(u"Amb aquest codi QR o bé amb l’enllaç ")}
                <a href="https://comparador.cnmc.gob.es/">comparador.cnmc.gob.es</a>
                ${_(u" pots consultar i comparar les diferents ofertes vigents de les comercialitzadores d’electricitat del mercat lliure.")}
            </div>
            <div class="cnmc_qr_image">
                <img
                    src="${addons_path}/som_polissa_condicions_generals/report/assets/generic_qr_comparator.png"
                />
            </div>
        </div>
    </div>
</%def>
