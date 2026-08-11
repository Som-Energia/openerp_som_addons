<%def name="summary_identification(holder, supply, self_consumption)">
<div class="summary-box-section">
    <div class="summary-box-section__title">${_(u"2. Identificació de la persona titular i del punt de subministrament")}</div>
    <div class="summary-box-group">
        <div class="summary-box ${'summary-box--third' if self_consumption else 'summary-box--half'}">
        <h3>${_(u"PERSONA TITULAR")}</h3>
        <div class="summary-content">
            <p class="section-text">- ${_(u"Nom o raó social:")} ${holder['name']}</p>
            <p class="section-text">- NIF/NIE/CIF: ${holder['vat']}</p>
            <p class="section-text section-text--wrap">- ${_(u"Adreça postal:")} ${holder['street']} ${holder['zip']} ${holder['city']}</p>
            <p class="section-text">- ${_(u"Telèfon:")} ${holder['phone'] or ''}</p>
            %if supply.get('cadastral_reference'):
                <p class="section-text" style="text-align: left">- ${_(u"Referència cadastral:")} ${supply['cadastral_reference']}</p>
            %endif
        </div>
        </div>

        <div class="summary-box ${'summary-box--third' if self_consumption else 'summary-box--half'}">
        <h3>${_(u"DADES DEL PUNT DE SUBMINISTRAMENT")}</h3>
        <div class="summary-content">
            <p class="section-text section-text--wrap">- ${_(u"Adreça:")} ${supply['address']}</p>
            <p class="section-text">- ${_(u"Província i país:")} ${supply['province']} ${supply['country']}</p>
            <p class="section-text">- CUPS: ${supply['cups']}</p>
            %if supply.get('contract_number'):
                <p class="section-text">- ${_(u"Número de pòlissa del contracte de subministrament:")} ${supply['contract_number']}</p>
            %endif
            <p class="section-text">- ${_(u"CNAE (codi nacional d'activitats econòmiques):")} ${supply['cnae']}</p>
        </div>
        </div>

        %if self_consumption:
        <div class="summary-box summary-box--third">
        <h3>${_(u"TIPOLOGIA DE L'AUTOCONSUM")}</h3>
        <div class="summary-content">
                %if self_consumption.get('cau'):
                    <p class="section-text">- CAU: ${self_consumption['cau']}</p>
                %endif
                <p class="section-text">- ${_(u"Col·lectiu S/N:")} ${'S' if self_consumption.get('collective') else 'N'}</p>
        </div>
        </div>
        %endif
    </div>
</div>
</%def>
