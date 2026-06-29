<%page args="company, holder, supply, self_consumption" />
<div class="summary-box">
    <h3>2. Identificación del titular y del punto de suministro</h3>
    <div class="summary-content">
        <p class="section-text inline-label">Datos persona titular</p>
        <p class="section-text">- Nombre o razón social: ${holder['name']}</p>
        <p class="section-text">- NIF/NIE/CIF: ${holder['vat']}</p>
        <p class="section-text">- Dirección postal: ${holder['street']} ${holder['zip']} ${holder['city']}</p>
        <p class="section-text">- Teléfono: ${holder['phone'] or ''}</p>
        %if supply.get('cadastral_reference'):
            <p class="section-text">- Referencia catastral: ${supply['cadastral_reference']}</p>
        %endif

        <div class="spacer"></div>
        <p class="section-text inline-label">Datos del punto de suministro</p>
        <p class="section-text">- Dirección: ${supply['address']}</p>
        <p class="section-text">- Provincia y país: ${supply['province']} ${supply['country']}</p>
        <p class="section-text">- CUPS: ${supply['cups']}</p>
        %if supply.get('contract_number'):
            <p class="section-text">- Número de póliza del contrato de suministro: ${supply['contract_number']}</p>
        %endif
        <p class="section-text">- CNAE (código nacional de actividades económicas): ${supply['cnae']}</p>

        %if self_consumption:
            <div class="spacer"></div>
            <p class="section-text inline-label">Tipología del autoconsumo</p>
            %if self_consumption.get('cau'):
                <p class="section-text">- CAU: ${self_consumption['cau']}</p>
            %endif
            <p class="section-text">- Colectivo S/N: ${'S' if self_consumption.get('collective') else 'N'}</p>
        %endif
    </div>
</div>
