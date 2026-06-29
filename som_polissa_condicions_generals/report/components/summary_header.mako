<%page args="company" />
<div class="summary-title">DOCUMENTO RESUMEN DEL CONTRATO DE SUMINISTRO ELÉCTRICO</div>
<div class="summary-box">
    <h3>1. Identificación de la empresa comercializadora</h3>
    <div class="summary-content">
        <p class="section-text"><span class="inline-label">Denominación social:</span> ${company['name']}</p>
        <p class="section-text"><span class="inline-label">Marca comercial:</span> ${company['brand']}</p>
        <p class="section-text"><span class="inline-label">NIF:</span> ${company['vat']}</p>
        <p class="section-text"><span class="inline-label">Dirección completa:</span> ${company['address']}</p>
        <p class="section-text"><span class="inline-label">Dirección postal:</span> ${company['postal_address']}</p>
        <p class="section-text"><span class="inline-label">Correo electrónico:</span> ${company['email']}</p>
        <p class="section-text"><span class="inline-label">Teléfono de atención gratuito:</span> ${company['phone']}</p>
    </div>
</div>
