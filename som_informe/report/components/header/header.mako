<%page args="d" />
    <h1>INFORME TÈCNIC</h1>
    <img src="https://www.somenergia.coop/wp-content/uploads/2020/12/171x107px_web_10_anys.gif">
    <a href="https://www.somenergia.coop/">www.somenergia.coop</a>

    ${_(u"Contracte Som Energia:")} ${d.contract_number}<br />
    ${_(u"Data d'alta amb Som Energia:")} ${d.data_alta}<br />

    ${_(u"Distribuidora:")} ${d.distribuidora}<br />
    ${_(u"Contracte Distribuidora:")} ${d.distribuidora_contract_number}<br />

    ${_(u"Nom del titular:")} ${d.titular_name}<br />
    ${_(u"DNI Titular:")} ${d.titular_nif} <br />
    ${_(u"CUPS:")} ${d.cups}<br />
    ${_(u"Adreça CUPS:")} ${d.cups_address}<br />

<h2>Cronologia:</h2>
<ul>