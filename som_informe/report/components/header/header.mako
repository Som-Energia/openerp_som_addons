<%page args="d" />
<img src="https://oficinavirtual.somenergia.coop/static/front/img/logo.png" alt="Logo SomEnergia"  width="200px"><br />
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
    ${_(u"<b>Potència contractada:</b>")} <b>${d.tarifa}</b>
    %if len(d.potencies) == 2:
        ${_(u" <b>Punta</b> %s; <b>Vall</b> %s") % (d.potencies[0]['potencia'],d.potencies[1]['potencia'])}<br />
    %elif d.potencies:
        % for pot in d.potencies[:-1]:
            ${_(u" <b>%s</b> %s;") % (pot['periode'], pot['potencia'])}
        %endfor
        ${_(u" <b>%s</b> %s") % (d.potencies[-1]['periode'], d.potencies[-1]['potencia'])}<br />
    %endif
    ${_(u"<b>Adreça CUPS:</b>")} ${d.cups_address}<br />
    ${_(u"<b>Data d'alta amb Som Energia:</b>")} ${d.data_alta}<br />
    %if d.data_baixa:
        ${_(u"<b>Data de baixa amb Som Energia:</b>")} ${d.data_baixa}<br />
    %endif
    ${_(u"<b>Titular:</b>")} ${d.titular_name}<br />
    ${_(u"<b>NIF Titular:</b>")} ${d.titular_nif} <br />
    <br />
