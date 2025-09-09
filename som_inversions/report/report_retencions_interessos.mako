# -*- coding: utf-8 -*-

<%
    import logging
    logger = logging.getLogger('openerp')
    report = objects[0]
    data = report.report_retencions_data()
%>

<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap" rel="stylesheet">
<head>
    <style type="text/css">
    body {
      margin: 5% 5% 5% 5%;
    }
    h1, h2, h3, p, ol, ul {
      font-family: Roboto;
      margin: 0px;
    }
    .capsalera{
      width: 100%;
      display: inline-block;
    }
    .fila {
      display: table-row;
    }
    .LogoPpal {
      display: table-cell;
      width: 20%;
      vertical-align: top;
      font-size: 0.9em;
      text-align: left;
    }
    .LogoPpal img {
      display: block;
      margin-left: 19px;
      margin-top: -10px;
    }
    .sotalogo {
      display: block;
      margin-top: -35px;
      padding: 0px 28px;
      font-size: 0.85em;
      line-height: 1.5em;
      max-width: 50%;
    }
    .TitolHeader {
      display: table-cell;
      vertical-align: top;
      max-width: 50%;
      float: right;
      margin-top: -175px;
    }
    h1.titol {
      text-align: right;
      font-size: 1.3em;
      margin-top:8px;
    }
    h2.titol {
      text-align: center;
      font-size: 1.1em;
      margin-bottom: 30px;
    }
    .caixaHeader {
      display: table-cell;
      background: #EDEEF0;
      border-bottom: 10px solid #BFC74D;
      width: 100%;
      padding-bottom: 15px;
      float: right;
    }
    .dreta, .esquerra {
      display: table-cell;
      width: 50%;
      height: 90px;
      margin: 0;
      padding: 0;
    }
    .caixaHeader .ContingutDades  {
      text-align: left;
      line-height: 1.4em;
      font-size: 0.85em;
    }
    .caixaHeader .doblecaixa {
      margin-bottom: -15px;
      padding-bottom: 0px;
    }
    .DataDoc {
      margin: 35px 0;
      text-align: right;
      font-size: 1em;
    }
    .TitolCaixa {
      background: #4D4D4D;
    }
    .TitolCaixa h2, .CaixaTitTitular h3,.CaixaTitAportacio h3, .InfoAddTitol h3 {
      font-weight: 900;
      font-size: 1em;
      color: white;
      padding: 8px 27px;
    }
    .CaixaFons {
      background: #EDEEF0;
    }
    .doblecaixa{
      width: 100%;
      display: table;
      /*margin-left: 0 auto;*/
      padding: 20px;
    }
    .CaixaTitTitular, .CaixaTitAportacio {
      display: table-cell;
      background: #BFC74D;
      color:white;
      width:48.5%;
      margin-top:0px;
    }
    .CaixaDadesTitular, .CaixaDadesAportacio {
      display: table-cell;
      background: white;
      padding: 30px 30px;
      line-height: 2.2em;
      font-size: 0.85em;
      text-align: justify;
      padding-bottom: 54px;
    }
    .footer {
      position: fixed;
      bottom: 3%;
      background: white;
      padding: 0px 30px;
      text-align: center;
      font-size: 0.85em;
      height: 2%;

    }
    @media print {
      footer {
        position:relative;
        top:-20px;
      }
    }
    </style>
</head>
<body>

    %for investment in objects :
    <%
    setLang(report.partner_id.lang)
    %>
<div class="capsalera">
  <div class="fila">
    <div class="LogoPpal">
      <a href="https://www.somenergia.coop" target="_blank">
        <img src="${addons_path}/som_inversions/report/logo.jpg" width="150" height="150"/ alt="Logo Som Energia"></a><br>
      <p class="sotalogo"><b>${data.somenergia.partner_name}</b><br>${_(u"CIF:")} ${data.somenergia.partner_vat.replace('ES','')}<br>${_(u"Domicili:")} ${data.somenergia.address_street} ${data.somenergia.address_zip} - ${data.somenergia.address_city}<br>
        ${_(u"Adreça electrònica:")} aporta@somenergia.coop
    </div>
  </div>
  <div class="TitolHeader">
    <h2 class="titol">${_(u"Comunicat de rendiments per a la")}<br/>${_(u"declaració de la RENDA ")}${data.year}</h2>
    <div class="caixaHeader">
      <div class="doblecaixa">
         <div class="fila">
            <div class="dreta">
               <p class="ContingutDades">
                  ${_(u"<b>Data:</b>")}<br/>
                  ${_(u"<b>Exercici:</b>")}<br/>
                  ${_(u"<b>Tipus d'aportació:</b>")}<br/>
               </p>
            </div>
            <div class="esquerra">
              <p class="ContingutDades">
                ${formatLang(time.strftime('%Y-%m-%d'), date=True)}<br/>
                ${data.year}<br>
                % if data.type == 'APO':
                   ${_("Aportacions voluntàries al capital social")}
                % elif data.type == 'TIT':
                   ${_("Títols participatius")}
                % endif
              </p>
            </div>
        </div>
    </div>
  </div>
</div>

</div>
<div class="DataDoc">

</div>
<div class="TitolCaixa">
  <h2></h2>
</div>

<div class="CaixaFons">
  <div class="doblecaixa">
    <div class="fila">
      <div class="CaixaTitTitular">
       <h3>${_(u"DADES DEL TITULAR")}</h3>
      </div>
      <div class="CaixaEspai">
      </div>
      <div class="CaixaTitAportacio">
       <h3>${_(u"INFORMACIÓ FISCAL")}</h3>
      </div>
    </div>
    <div class="fila">
      <div class="CaixaDadesTitular">
        <p class="ContingutDades"><b>${_(u"Nom:")}</b> ${data.partner_name}<br><b>${_(u"NIF/NIE:")}</b> ${data.partner_vat}
        </p>
      </div>
      <div class="CaixaEspai">
      </div>
      <div class="CaixaDadesAportacio">
        <p class="ContingutDades"><b>${_(u"Rendiments bruts:")}</b> ${formatLang(data.amount_untaxed, monetary=True)} €<br>
        <b>${_(u"19% Retenció sobre l'estalvi:")}</b> ${formatLang(data.amount_tax, monetary=True)} €<br>
        <b>${_(u"Tipus percepció:")}</b> ${_(u"Dinerària")}</p>
      </div>
    </div>
    <p style="padding-top:15px;"><b>${_(u"Saldo a ")}${formatLang(data.date_last_date_previous_year, date=True)}:</b> ${formatLang(data.balance, monetary=True)} €</p>
  </div>
</div>
<div>
  <div class="footer">
    <p class="TextPeu">${_(u"Som Energia, SCCL, CIF F55091367 | Domicili Riu Güell, 68 - 17005 - Girona | aporta@somenergia.coop | www.somenergia.coop")}</p>
  </div>
</div>

    %endfor
</body>
</html>
