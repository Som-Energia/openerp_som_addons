<%
    inv = objects[0]
    data = inv.report_liquidacions_titols_data()
    setLang(inv.partner_id.lang)
%>

<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<head>
    <style type="text/css">
    ${css}
    body {
      margin: 5% 7% 5% 7%;
    }
    h1, h2, h3, p, ol, ul {
      font-family: Roboto;
      margin: 0px;
    }
    h1 {
      text-transform: uppercase;
    }
    .capsalera{
      width: 100%;
      display: table;
    }
    .fila {
      display: table-row;
    }
    .filesInternes {
      display: flex;
      height: 80px;
    }
    .LogoPpal {
      padding-top: 1rem;
      margin-top: 1rem;
      display: table-cell;
      vertical-align: top;
      text-align: left;
    }
    .LogoPpal img {
      display: block;
      margin-top: -10px;
    }
    .sotalogo {
      width: 250px;
      margin-top: -5px;
      margin-left: -20px;
      padding: 0px 28px;
      font-size: 0.65em;
      line-height: 1.5em;
    }
    .TitolHeader {
      position: absolute;
      top: 11rem;
      right: 7%;
      display: table-cell;
      vertical-align: top;
      margin-top: -175px;
    }
    h1.titol {
      width: 400px;
      text-align: right;
      font-size: 1.1em;
    }
    h2.titol {
      width: 400px;
      text-align: right;
      font-size: 0.9em;
      margin-bottom: 10px;
    }
    .caixaHeader {
      background: #EDEEF0;
      border-bottom: 10px solid #BFC74D;
      width: 300px;
      float: right;
    }
    .dreta {
      width: 50%;
    }
    .dreta, .esquerra {
      display: table-cell;
      width: 50%;
      margin: 0;
      padding: 0;
    }

    .caixaHeader .ContingutDades  {
      text-align: left;
      line-height: 1.4em;
      font-size: 0.65em;
    }
    .caixaHeader .doblecaixa {
      padding-bottom: 15px;
    }
    .DataDoc {
      margin: 30px 0;
      text-align: right;
      font-size: 1em;
    }
    .TitolCaixa {
      margin-top: 50px;
      background: #0B2E34;
    }
    .TitolCaixa h2, .CaixaTit h3, .CaixaTitNum h3 {
      font-size: 0.55em;
      color: white;
      padding: 8px 12px;
    }
    .CaixaFons {
      background: #EDEEF0;
      padding: 15px;
    }
    .doblecaixa{
      width: 93%;
      display: table;
      margin-left: 15px;
      padding-top: 15px;
      padding-bottom: 15px;
    }
    .cinccaixes {
      display: table;
      margin: 0 auto;
    }

    .CaixaTit {
      display: table-cell;
      background: #BFC74D;
      color:white;
      width:15%;
      margin-top:0px;
    }
    .CaixaTitNum {
      display: table-cell;
      background: #BFC74D;
      color:white;
      width:30%;
      margin-top:0px;
      text-align: right;
    }
    .CaixaDades {
      display: table-cell;
      background: white;
      padding: 15px 10px 0px 10px;
      line-height: 1.1em;
      font-size: 0.55em;
      text-align: justify;
    }
    .CaixaDadesFilaSegona {
      display: table-cell;
      background: white;
      padding: 10px 12px;
      line-height: 1.5em;
      font-size: 0.85em;
      text-align: justify;
    }
    .CaixaDades .ContingutDades {
      text-align: center;
    }
    .CaixaDades .numeracio {
      text-align: right;
    }
    .paragraf p {
      padding-left: 12px;
      line-height: 1.5em;
      font-size: 0.65em;
    }
    .espaiTancament{
      margin: 300px 0px;
      background: white;
    }
    .final {
      padding: 12px;
    }
    .footer {
      position: absolute;
      bottom: 0;
      width: 84%;
      height: 3rem;
      background: white;
      padding: 0px;
      text-align: center;
      font-size: 0.65em;
    }

    </style>
</head>
<body>
    <div class="capsalera">
    <div class="fila">
        <div class="LogoPpal">
        <a href="https://www.somenergia.coop" target="_blank">
        <!-- 150px mida logo -->
        <img src="${addons_path}/som_inversions/report/logo2.svg" alt="Logo Som Energia" width="150" height="75" /></a><br>
        <p class="sotalogo"><b>${data.somenergia.partner_name}</b><br>${_(u"CIF:")} ${data.somenergia.partner_vat.replace('ES','')}<br>${_(u"Domicili:")} ${data.somenergia.address_street} ${data.somenergia.address_zip} - ${data.somenergia.address_city}<br>
            ${_(u"Adreça electrònica:")} <a href="mailto:aporta@somenergia.coop">${_(u"aporta@somenergia.coop")}</a>
    </div>
        <div class="TitolHeader">
        <h1 class="titol">${_(u"Liquidació interessos")}</h1>
        <h2 class="titol">${_(u"Comunicat dels interessos generats  per les teves aportacions")}</h2>
        <div class="caixaHeader">
            <div class="doblecaixa">
            <div class="fila">
                <div class="dreta">
                    <p class="ContingutDades">
                        <b>${_(u"Tipus d'aportació:")}</b><br/>
                        <b>${_(u"Titular:")}</b><br/>
                        <b>${_(u"NIF:")}</b>
                    </p>
                </div>
            <div class="esquerra">
                <p class="ContingutDades">
                    ${_(u"Títols participatius")}<br/>
                    ${data.partner_name}<br/>
                    ${data.partner_vat.replace('ES','')}
                    </p>
                </div>
        </div>
        </div>
        </div>
    </div>
    </div>
    </div>

    <div class="DataDoc">

    </div>

    <div class="TitolCaixa">
        <h2>${_(u"LIQUIDACIÓ INTERESSOS")}</h2>
    </div>

    <div class="CaixaFons">
    <div class="cinccaixes">
        <div class="fila">
        <div class="CaixaTit">
            <h3>${_(u"DATA INICIAL")}</h3>
        </div>
        <div class="CaixaEspai"></div>
        <div class="CaixaTit">
            <h3>${_(u"DATA FINAL")}</h3>
        </div>
        <div class="CaixaEspai"></div>
        <div class="CaixaTit">
            <h3>${_(u"SALDO APORTAT")}</h3>
        </div>
        <div class="CaixaEspai"></div>
        <div class="CaixaTitNum">
            <h3>${_(u"TIPUS INTERÈS")}</h3>
        </div>
        <div class="CaixaEspai"></div>
        <div class="CaixaTitNum">
            <h3>${_(u"INTERESSOS GENERATS")}</h3>
        </div>
        <div class="CaixaEspai"></div>
        </div> <!-- Títols caixa -->

        %for line in data.lines:
        <div class="fila">
        <div class="CaixaDades">
            <p class="ContingutDades">${line.date_ini}</p>
        </div>
        <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades">${line.date_end}</p>
        </div>
    <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades">${formatLang(line.quantity, monetary=True)} €</p>
        </div>
    <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">${formatLang(line.interest_type,monetary=True)} %</p>
        </div>
    <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">${formatLang(line.generated_interests, monetary=True)} €
        </div>
        </div> <!-- Primera línia de text -->
        %endfor

        <div class="fila">
        <div class="CaixaDades">
            <p class="ContingutDades"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">${_(u"TOTAL INTERESSOS:")}
            </p>
        </div>
        <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">${formatLang(data.total, monetary=True)} €
            </p>
        </div>
        <div class="CaixaEspai">
        </div>
        </div>
        <div class="fila">
        <div class="CaixaDades">
            <p class="ContingutDades"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades"></p></div>
        <div class="CaixaEspai"></div>
        %for tax_line in data.tax_lines:
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">${_(u"RETENCIONS")} ${tax_line.name}
            </p>
        </div>
        <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">${formatLang(tax_line.amount, monetary=True)} €
            </p>
        </div>
        %endfor
        <div class="CaixaEspai">
        </div>
        </div>
        <div class="fila">
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"><b>${_(u"IMPORT A ABONAR:")}</b>
            </p>
        </div>
        <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"><b>${formatLang(data.to_pay_total,monetary=True)} €</b>
            </p>
        </div>
        <div class="CaixaEspai">
        </div>
        </div>
        <div class="fila">
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio"></p></div>
        <div class="CaixaEspai"></div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">
            </p>
        </div>
        <div class="CaixaEspai">
        </div>
        <div class="CaixaDades">
            <p class="ContingutDades numeracio">
            </p>
        </div>
        <div class="CaixaEspai">
        </div>
        </div> <!-- espai en blanc final -->
    </div>
    </div>
    <div class="contingutTXT">
            <div class="paragraf">
            <p style="margin-top:60px;">${_(u"Aquest import serà transferit al teu compte corrent número:")}   <b>${(data.partner_iban[:-9] or '')}***</b>.</p>
            <p>${_(u"Actualment les teves aportacions en títols participatius de SOM ENERGIA SCCL sumen")}   <b>${formatLang(abs(inv.partner_id.property_account_titols.balance),monetary=True)} €</b>. </p>
            <p style="margin-top:20px;">${_(u"Gràcies a les aportacions com la teva, la cooperativa finança projectes i pot generar cada vegada més energia provinent de fonts renovables.")}</p>
            </div>
    </div>
    <div class="espaiTancament"></div>
    <div class="footer">
        <p class="TextPeu">${data.somenergia.partner_name} CIF ${data.somenergia.partner_vat.replace('ES','')} | ${data.somenergia.address_street} - ${data.somenergia.address_zip} - ${data.somenergia.address_city} | aporta@somenergia.coop | www.somenergia.coop</p>
    </div>
    </div>
</body>
</html>
