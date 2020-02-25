## -*- coding: utf-8 -*-
<%
from datetime import datetime, date
from math import ceil
%>
<!doctype html>
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<head>
<style type="text/css">
body {
  margin: 5% 10% 5% 20%;
}
h1, h2, h3, p, ol, ul {
  font-family: Roboto;
  margin: 0px;
}
.capsalera{
  width: 100%;
  display: table;
}
.fila {
  display: table-row;
}
.LogoPpal {
  display: table-cell;
  width: 35%;
  vertical-align: top;
  text-align: left;
}
.LogoPpal img {
  display: block;
  margin-left: 19px;
}
.sotalogo {
  margin-top: -5px;
  padding: 0px 28px;
  font-size: 0.8em;
  line-height: 1.5em;
}
.TitolHeader {
  display: table-cell;
  vertical-align: top;
}
h1.titol {
  text-align: right;
  font-size: 1.5em;
  margin-top:8px;
  margin-bottom: 46px;
}
.caixaHeader {
  background: #EDEEF0;
  border-bottom: 10px solid #BFC74D;
  padding: 5px 5px 2px 20px;
  width: 80%;
  float: right;
  
}
.textcaixa {
  text-align: justify;
  font-size: 0.85em;
  line-height: 1.5em;
  font-weight:200;
}
.DataDoc {
  margin: 70px 0;
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
  width: 95%;
  display: table;
  margin-left: 27px;
  padding-top:20px;

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
}

.CaixaUnica {
  width: 95%;
  display: table;
  margin-left: 27px;
  padding-top:20px;
  padding-bottom:30px;
}
.InfoAddTitol {
  display: table-row;
  background: #BFC74D;
  color:white;
  width:100%;
  margin-top:0px;
}
.InfoAddTxt {
  display: table-row;
  background: white;
  width:100%;
  margin-top:0px;
  line-height: 2.2em;
  font-size: 0.85em;
}
.TextFormula {
  text-align:left;
  padding: 30px 30px 0px 30px;
}
.TextExplica {
  text-align:center;
  padding: 20px 0 10px 0;
}
.TextInfo {
  text-align: justify;
  padding: 10px 30px;
}
.TextInfo2 {
  text-align: justify;
  padding: 5px 30px 20px 30px;
}
.TitolCondicions {
  text-transform: uppercase;
  font-weight: 900;
  padding: 30px 30px 10px 30px;
  font-size: 0.85em;
}
.sagnia {
  text-indent: -24px;
  padding-left: 52px;
  padding-right: 30px;
  padding-bottom: 5px;
  font-size: 0.85em;
  text-align: justify;
}
.alpha {
    counter-reset: alpha;
    list-style-type: none;
}
.alpha > li {
    text-indent: -14px;
    padding-left: 27px;
    margin-top: 3px;
    padding-right: 30px;
  padding-bottom: 10px;
  font-size: 0.85em;
  text-align: justify;
}
.alpha > li:before {
    counter-increment: alpha;
    content: counter(alpha, lower-alpha)") ";
}
.punts {
  display: block;
  list-style-type: disc;
  padding-left: 72px;
  padding-bottom: 10px;
  font-size: 0.85em;
  margin-top:5px;
}
.punts > li {
  text-indent:0;
}
.final {
  padding: 20px;
}
.footer {
  position:relative;
  top:-20px;
  background: white;
  padding: 30px 0px;
  text-align: center;
  font-size: 0.85em;
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
%for inv in objects :
<% setLang(inv.partner_id.lang)

month_names = [_('gener'), _('febrer'), _('març'), _('abril'), _('maig'),
               _('juny'), _('juliol'), _('agost'), _('setembre'), _('octubre'),
               _('novembre'), _('desembre')]

investment = inv.pool.get('generationkwh.investment')
investment_id = investment.search(inv._cr, inv._uid, [('name','=',inv.origin)])
investment_obj = investment.read(inv._cr, inv._uid, investment_id)
purchase_date = investment_obj[0]['purchase_date']
contract_date = datetime.strptime((purchase_date!='' and purchase_date)
				   or (inv.date_invoice!='' and date_invoice) \
                                   or date.today().strftime('%Y-%m-%d'),
                                   '%Y-%m-%d')
nshares = investment_obj[0]['nshares']
amount = int(nshares * 100)
num_accions = nshares
perm_data = inv.perm_read()[0]
creation_date = datetime.strptime(perm_data['create_date'], '%Y-%m-%d %H:%M:%S.%f')
creation_date_str = creation_date.strftime(_('%d/%m/%Y a les %T'))
%>
<%def name="signatures(inv)">
<div class="signatures_block">
    <h3>${_(u"Data del contracte:")}</h3>
    <p class="data">${contract_date.day} de ${month_names[contract_date.month-1]} de ${contract_date.year}</p>
    <p>${_("Aquest contracte noms ser actiu un cop el pagament corresponent s'hagi fet efectiu")}</p>

    <div class="signatures">
        <div class="signatura">
            <ul>
                <li><b>Som Energia, SCCL</b></li>
                <li><img src="${addons_path}/som_inversions/report/firma_cb.png" height="150" width="200"/></li>
                <li><b>${_(u"Signat:")} Carles Barbar Puig</b></li>
            </ul>
        </div>
        <div class="signatura">
            <ul>
                <li><b>${_(u"El Soci/La Scia")}</b></li>
                <li class="signature_text">${_('Condicions acceptades a travs del formulari web el dia %s') % creation_date_str}</li>
                <li><b>${_(u"Signat:")} ${inv.partner_id.name or ''}</b></li>
            </ul>
        </div>
    </div>
</div>
</%def>
<div>
    <img class="logo" src="${addons_path}/som_inversions/report/logo.jpg" width="150" height="150"/>
</div>
<div class="contracte">
    <h1>${_(u"CONTRACTE D'ADHESIÓ AL SISTEMA D'AUTOPRODUCCIO COLLECTIVA D'ENERGIA ELCTRICA PROVINENT DE FONTS RENOVABLES")}</h1>
    ${signatures(inv)}
</div>
<p style="page-break-after:always"></p>
<div class="contracte_llarg">

    ${signatures(inv)}
</div>
<p style="page-break-after:always"></p>
%endfor
</body>
</html>
