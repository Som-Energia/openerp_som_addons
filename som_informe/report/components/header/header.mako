<%page args="d" />
<h1>${_(u"INFORME TÈCNIC")}</h1>
    <img src="https://www.somenergia.coop/wp-content/uploads/2020/12/171x107px_web_10_anys.gif" ><br />
    <a href="https://www.somenergia.coop/">www.somenergia.coop</a><br />
    <br />
    ${_(u"Contracte Som Energia:")} ${d.contract_number}<br />
    ${_(u"Data d'alta amb Som Energia:")} ${d.data_alta}<br />
    ${_(u"Distribuidora:")} ${d.distribuidora}<br />
    ${_(u"Contracte Distribuidora:")} ${d.distribuidora_contract_number}<br />
    ${_(u"Nom del titular:")} ${d.titular_name}<br />
    ${_(u"DNI Titular:")} ${d.titular_nif} <br />
    ${_(u"CUPS:")} ${d.cups}<br />
    ${_(u"Adreça CUPS:")} ${d.cups_address}<br />
    <br />
<h2>${_(u"Cronología:")}</h2>
    <ul>