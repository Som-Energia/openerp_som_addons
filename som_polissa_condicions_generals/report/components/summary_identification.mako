<%def name="summary_identification(holder, supply, self_consumption)">
<div class="summary-box-section">
    <div class="summary-box-section__title">2. Identificación del titular y del punto de suministro</div>
    <div class="summary-box-group">
        <div class="summary-box ${'summary-box--third' if self_consumption else 'summary-box--half'}">
        <h3>PERSONA TITULAR</h3>
        <div class="summary-content">
            <p class="section-text">- Nombre o razón social: ${holder['name']}</p>
            <p class="section-text">- NIF/NIE/CIF: ${holder['vat']}</p>
            <p class="section-text section-text--wrap">- Dirección postal: ${holder['street']} ${holder['zip']} ${holder['city']}</p>
            <p class="section-text">- Teléfono: ${holder['phone'] or ''}</p>
            %if supply.get('cadastral_reference'):
                <p class="section-text">- Referencia catastral: ${supply['cadastral_reference']}</p>
            %endif
        </div>
        </div>

        <div class="summary-box ${'summary-box--third' if self_consumption else 'summary-box--half'}">
        <h3>DATOS DEL PUNTO DE SUMINISTRO</h3>
        <div class="summary-content">
            <p class="section-text section-text--wrap">- Dirección: ${supply['address']}</p>
            <p class="section-text">- Provincia y país: ${supply['province']} ${supply['country']}</p>
            <p class="section-text">- CUPS: ${supply['cups']}</p>
            %if supply.get('contract_number'):
                <p class="section-text">- Número de póliza del contrato de suministro: ${supply['contract_number']}</p>
            %endif
            <p class="section-text">- CNAE (código nacional de actividades económicas): ${supply['cnae']}</p>
        </div>
        </div>

        %if self_consumption:
        <div class="summary-box summary-box--third">
        <h3>TIPOLOGIA DEL AUTOCONSUMO</h3>
        <div class="summary-content">
                %if self_consumption.get('cau'):
                    <p class="section-text">- CAU: ${self_consumption['cau']}</p>
                %endif
                <p class="section-text">- Colectivo S/N: ${'S' if self_consumption.get('collective') else 'N'}</p>
        </div>
        </div>
        %endif
    </div>
</div>
</%def>
