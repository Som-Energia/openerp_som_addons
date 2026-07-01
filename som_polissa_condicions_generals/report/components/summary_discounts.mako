<%def name="summary_discounts(discounts)">
<div class="summary-box">
    <h3>5. Descuentos y promociones</h3>
    <div class="summary-content">
        %if discounts['show_legal_text']:
            <p class="section-text">${discounts['text']}</p>
            <p class="section-text">En caso de que te queden SOLS pendientes de aplicación y que te den derecho al descuento, estos caducarán a los 5 años desde la fecha de factura donde consta su emisión.</p>
            <p class="section-text">En caso de que des de baja del punto de suministro, cambio de comercializador, traspaso o subrogación del contrato los SOLS y descuentos pendientes de aplicación se perderán automáticamente.</p>
        %else:
            <p class="section-text">${discounts['text']}</p>
        %endif
    </div>
</div>
</%def>
