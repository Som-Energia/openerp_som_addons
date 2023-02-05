<%page args="d" />
<img src="https://www.somenergia.coop/wp-content/uploads/2014/11/logo-somenergia.png" width="200px"><br />
<h1>${_(u"INFORME TÈCNIC")}</h1>
    <br />
    ${_(u"<b>Contracte Som Energia:</b>")} ${d.contract_number}<br />
    ${_(u"<b>Empresa distribuïdora:</b>")} ${d.distribuidora}<br />
    ${_(u"<b>Contracte distribuïdora:</b>")}
    %if d.distribuidora_contract_number:
        ${d.distribuidora_contract_number}<br />
    %else:
        <br/>
    %endif
    ${_(u"<b>CUPS:</b>")} ${d.cups}<br />
    ${_(u"<b>Potència contractada:</b>")} ${d.contracted_energy}<br />
    ${_(u"<b>Adreça CUPS:</b>")} ${d.cups_address}<br />
    ${_(u"<b>Data d'alta amb Som Energia:</b>")} ${d.data_alta}<br />
    %if d.data_baixa:
        ${_(u"<b>Data de baixa amb Som Energia:</b>")} ${d.data_baixa}<br />
    %endif
    ${_(u"<b>Titular:</b>")} ${d.titular_name}<br />
    ${_(u"<b>NIF Titular:</b>")} ${d.titular_nif} <br />
    <br />
