## -*- coding: utf-8 -*-
<%
from datetime import datetime, date
from math import ceil
report = objects[0]
data = report.investmentCreationAPO_notificationData()
%>
<!doctype html>
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
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
  margin: 60px 0;
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
  padding: 8px 27px;20
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
<link href="https://fonts.googleapis.com/css?family=Roboto:300,400,700,900&display=swap" rel="stylesheet">
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

conf_obj = inv.pool.get('res.config')
interest_rate = float(conf_obj.get(inv._cr, inv._uid, 'som_aportacions_interest', 0))
%>
<link href="https://fonts.googleapis.com/css?family=Roboto:300,400,700,900&display=swap" rel="stylesheet">


<div class="capsalera">
  <div class="fila">
    <div class="LogoPpal">
    <a href="https://www.somenergia.coop" target="_blank">
      <img src="https://www.somenergia.coop/iconespdf/logo_som_energia.svg" alt="Logo Som Energia" width="200" height="100" /></a><br>
      <p class="sotalogo"><b>${_(u"Som Energia, SCCL")}</b><br>${_(u"CIF: F55091367")}<br>${_(u"Domicili: C/Riu Güell, 68. 17005- Girona")}<br>
${_(u"Adreça electrònica: aporta@somenergia.coop")}
  </div>
    <div class="TitolHeader">
    <h1 class="titol">${_(u"CONDICIONS DE LES APORTACIONS")}<br>
        ${_(u"VOLUNTÀRIES AL CAPITAL SOCIAL")}</h1>
    <div class="caixaHeader">
      <p class="textcaixa">${_(u"L’aportació està subjecta a les prescripcions previstes a la Llei de cooperatives de Catalunya (Llei 12/2015 de 9 de juliol), als Estatuts socials vigents de la cooperativa i als acords de l’Assemblea general de Som Energia, SCCL.")}</p>
    </div>
  </div>
  </div>
</div>

<div class="DataDoc">
  <p>${_(u"Girona, a ")}${data.invoiceDate}</p>
</div>

<div class="TitolCaixa">
     <h2>${_(u"CONDICIONS PARTICULARS DE L’APORTACIÓ AL CAPITAL SOCIAL")}</h2>
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
         <h3>${_(u"DADES DE L'APORTACIÓ")}</h3>
      </div>
    </div>
    <div class="fila">
      <div class="CaixaDadesTitular">
    <p class="ContingutDades"><b>${_(u"Titular:")}</b> ${data.ownerName}<br><b>${_(u"DNI/NIE:")}</b> ${data.ownerNif}<br><b>${_(u"Adreça fiscal:")}</b> ${data.partnerAddress}<br><b>${_(u"Correu electrònic:")}</b> ${data.partnerEmail}</p>
  </div>
      <div class="CaixaEspai">
      </div>
      <div class="CaixaDadesAportacio">
         <p class="ContingutDades"><b>${_(u"Data d'aportació:")}</b> ${data.inversionOrderDate}<br><b>${_(u"Venciment:")}</b> ${_(u"Indefinit.")}<br><b>${_(u"Sol·licitud de cancel·lació:")}</b> ${_(u"En qualsevol moment.")}<br><b>${_(u"Import:")}</b> ${data.inversionInitialAmount} €<br><b>${_(u"Remuneració:")}</b> ${interest_rate}% ${_(u"interès nominal anual (revisable anualment per l'Assemblea general).")}<br><b>${_(u"Meritació d’interessos:")}</b> ${_(u"Anual, de l’1 de juliol al 30 de juny.")}<br><b>${_(u"Pagament:")}</b> ${_(u"Anual, durant el mes de juliol de l’any següent.")}</p>
</div>
    </div>
  </div>
<div style="page-break-after: always">
</div>
    <div class="CaixaUnica">
    <div class="InfoAddTitol">
      <h3>${_(u"INFORMACIÓ ADDICIONAL")}</h3>
   </div>
    <div class="InfoAddTxt">
      <p class="TextFormula">${_(u"Fórmula per determinar l’import absolut de la remuneració meritada:")}</p>
      <p class="TextExplica">${_(u"I = ((A*%I)/365)*D<br>I= interessos &nbsp;&nbsp; &nbsp; &nbsp; A= aportació&nbsp; &nbsp; &nbsp; &nbsp; D= dies")}</p>
  <p class="TextInfo">${_(u"Aportació disponible en qualsevol moment amb 3 mesos de preavís mitjançant l'enviament de correu electrònic a aporta@somenergia.coop sens perjudici de l'establert a la resta de condicions i als Estatuts. L’any 2019 l’Assemblea general va aprovar la possibilitat que el Consell Rector pugui refusar incondicionalment el reemborsament de les aportacions voluntàries quan les sol·licituds de reemborsament superin el 10% del capital social existent a la data d’inici de l’exercici econòmic o superin el límit anual d' 1.350.000 euros (vegeu les condicions generals i els Estatuts).")}</p>
  <p class="TextInfo2">${_(u"Aquest contracte s’activarà quan es faci efectiu el pagament corresponent.")}</p>
  </div>
      <div class="final"></div>
   </div>
  
</div>
<div style="page-break-after: always">
</div>
<!-- Pàgina 2 -->
<div class="TitolCaixa">
     <h2>${_(u"CONDICIONS GENERALS DE LES APORTACIONS VOLUNTÀRIES AL CAPITAL SOCIAL")}</h2>
</div>
<div class="CaixaFons">
  <p class="TitolCondicions">${_(u"1. objecte")}</p>
<p class="sagnia">${_(u"1.1 D’acord amb el que preveuen els Estatuts de SOM ENERGIA, SCCL, i les decisions adoptades pels seus òrgans cooperatius, el capital social està constituït per les aportacions obligatòries de les persones sòcies, i també per aportacions voluntàries.")}</p> 
<p class="sagnia">${_(u"1.2 En cap cas s’inclou en aquestes condicions els títols participatius i el Generation kWh. Tampoc podran accedir a subscriure aquestes aportacions voluntàries aquelles persones que no hagin estat acceptades prèviament com persones sòcies.")}</p>  

<p class="sagnia">${_(u"1.3 La persona sòcia ha de posseir com a mínim un títol que es desemborsarà de manera íntegra al moment de formalització de la subscripció. Totes les aportacions es destinaran al desenvolupament de la cooperativa, en concret, a afavorir la comercialització i producció d’energia elèctrica provinent de fonts renovables.")}</p>
  <p class="TitolCondicions">${_(u"2. VALOR NOMINAL DE CADA APORTACIÓ")}</p>
  <p class="sagnia">${_(u"2.1 El valor mínim de les aportacions serà de cent euros (100€). Durant la primera setmana es limitaran les aportacions a cinc mil euros (5.000€) per persona sòcia, per tal de donar l'oportunitat a més socis a participar. Si no s’arriba al total requerit, s’ampliarà l’aportació fins als cent mil euros (100.000€) per cada persona sòcia. A efectes de computar aquest màxim de 100.000 euros, es comptaran totes les aportacions al capital social voluntari que la persona sòcia hagi efectuat amb anterioritat.")}</p> 

<p class="sagnia">${_(u"2.2 Les aportacions s’acrediten mitjançant títols nominatius, llibretes, fitxes o relació nominal de socis amb el seu import corresponent, diferents per a unes o altres aportacions, i no tenen en cap cas la consideració de títols valors.")}</p>
  <p class="TitolCondicions">${_(u"3. INTERESSOS")}</p>
  <p class="sagnia">${_(u"3.1 Les aportacions voluntàries al capital social de SOM ENERGIA SCCL generaran els interessos que determini de forma anual l’Assemblea sense que s’hagi preestablert cap interès mínim, encara que en cap cas podran superar l’interès legal del diner.")}</p>
  <p class="sagnia">${_(u"3.2 La data a partir de la qual començaran a meritar els interessos a favor de la persona sòcia serà la del dia següent al desemborsament efectiu de l’import corresponent a les aportacions subscrites. Per “desemborsament efectiu” s’entén el dia de l’abonament del capital voluntari al compte de SOM ENERGIA SCCL.")}</p>
  <p class="TitolCondicions">${_(u"4. TRASPÀS")}</p>
  <p class="sagnia">${_(u"4.1 La persona sòcia pot traspassar les aportacions voluntàries per les causes següents, d’acord amb el que s’estableix a la Llei 18/2015 de cooperatives de Catalunya:")}</p>
<ol class="alpha">
  <li>${_(u"Per actes “inter vivos”, entre persones sòcies, i en els termes establerts als estatuts socials, i en exposició al tauler d’anuncis de la cooperativa, amb autorització prèvia del Consell Rector.")}</li> 
  <li>${_(u"Per actes “mortis causa”, els hereus substitueixen a la persona causant en la seva posició jurídica, subrogant-se en els drets i les obligacions que tenia cap a la cooperativa.")}</li>
  </ol>
<p class="TitolCondicions">${_(u"5. RETORN DE LES APORTACIONS VOLUNTÀRIES")}</p>
<p class="sagnia">${_(u"5.1 L’aportació voluntària al capital de SOM ENERGIA, SCCL, romandrà a la cooperativa fins que la persona sòcia en sol·liciti el retorn, sens perjudici del que s'estableix a la Llei i els Estatuts socials per a les aportacions el reemborsament de les quals pugui ser refusat incondicionalment pel Consell Rector.")}</p> 
<p class="sagnia">${_(u"5.2 La persona sòcia té dret a sol·licitar a SOM ENERGIA, SCCL, el retorn de les aportacions en qualsevol moment.")}</p>
<p class="sagnia">${_(u"5.3 D’acord amb els Estatuts de SOM ENERGIA, SCCL, que en qualsevol cas prevaldran sobre aquestes clàusules, el Consell Rector estarà obligat a acordar el reemborsament de les aportacions voluntàries fins al límit del 10% del capital social existent a la data d’inici de l’exercici econòmic en cas que se sol·liciti el reemborsament, i sempre amb el límit anual d‘1.350.000 euros, en els terminis establerts al punt 5.6. En els casos que les sol·licituds excedeixin aquest límit, els nous reemborsaments estan condicionats a l’acord favorable del Consell Rector que, conforme als Estatuts de la cooperativa, serà lliure per refusar-los incondicionalment.")}</p>
<p class="sagnia">${_(u"5.4 En cas de baixa d’una persona sòcia, aquesta té el dret de sol·licitar el reemborsament de les seves aportacions voluntàries, sens perjudici del que la llei i els estatuts socials estableixen. En aquest cas els criteris que s’aplicaran de conformitat amb els Estatuts socials seran els següents:")}</p>
<ol class="alpha">
<li>${_(u"a) En el termini d'un mes de l'aprovació dels comptes anuals de l'exercici en què causi baixa la persona sòcia, s'ha de procedir a fixar l'import definitiu del reemborsament de les seves aportacions al capital social, sobre la base de l'exercici econòmic en què es produeixi la baixa i, si escau, de la imputació de resultats que li sigui atribuïble. El Consell Rector pot fixar un import provisional abans de l'aprovació dels comptes i, si convé, autoritzar un reemborsament a compte del definitiu.")}</li>
<li>${_(u"b) De l'import definitiu del reemborsament resultant, d'acord amb el paràgraf anterior, s'han de fer les deduccions següents, quan convingui:")}<br>
<ul style="list-style-type: disc;">
  <li>${_(u"Totes les quantitats que la persona sòcia degui a la cooperativa, per qualsevol concepte.")}</li>
  <li>${_(u"Les procedents per baixa no justificada o expulsió.")}</li>
  <li>${_(u"Les responsabilitats que li poden ser imputades i quantificades, sense perjudici de la responsabilitat patrimonial en virtut del que estableixi la Llei de cooperatives de Catalunya.")}</li>
  </ul>
</ol>
<p class="sagnia">${_(u"5.5 A més del que preveuen els paràgrafs precedents, es poden fer les deduccions següents:")}</p>
<ol class="alpha">
  <li>${_(u"a) Si la baixa és justificada no es fa cap deducció.")}</li>
  <li>${_(u"b) No hi pot haver deduccions sobre les aportacions voluntàries.")}</li>
</ol>
<p class="sagnia">${_(u"5.6 La cooperativa ha d’efectuar el pagament de les aportacions socials en el termini pactat per mutu acord amb la persona sòcia i, en defecte, en el termini que assenyali el Consell Rector i que no pot ser superior als cinc anys comptats des de la baixa de la persona sòcia o bé des de la data en que el Consell Rector hagi acordat el reemborsament segons l’article 35.4 de la Llei 12/2015 de cooperatives de Catalunya. Durant aquest temps, la persona sòcia que causa la baixa té dret a percebre l'interès legal del diner per la quantia pendent de reemborsament.")}</p>
<p class="TitolCondicions">${_(u"6. RESPONSABILITAT")}</p>
<p class="sagnia">${_(u"6.1 La responsabilitat de la persona sòcia per les obligacions socials és limitada a les aportacions al capital subscrites, tant si són desemborsades, com si no, sens perjudici del que disposen els Estatuts socials i la Llei de cooperatives.")}</p>

<p class="sagnia">${_(u"6.2 La persona sòcia que es doni de baixa continua sent responsable durant cinc anys davant la cooperativa, amb la limitació esmentada al paràgraf anterior, per les obligacions assumides per aquesta amb anterioritat a la data de la baixa.")}</p>
<div class="final"></div>
</div>
<div class="CaixaFons">  
<p class="TitolCondicions">${_(u"7. DRET DE DESISTIMENT")}</p>  
<p class="sagnia">${_(u"7.1 Totes les persones sòcies que formalitzin aquest contracte disposaran de 14 dies naturals des de la data del contracte per desistir dels serveis. En cas que es vulgui desistir, serà necessària la notificació a través del correu electrònic o postal, determinat a les Condicions Generals previstes al mateix web de contractació o bé directament a aporta@somenergia.coop.")}</p>

<p class="sagnia">${_(u"7.2 En cas d’exercir el dret de desistiment SOM ENERGIA, SCCL, s’obliga a retornar, dins del termini de 14 dies naturals des de la notificació formal de la persona sòcia, l’aportació voluntària seguint el mateix mètode de pagament que la persona sòcia hagi utilitzat, excepte una altra indicació.")}</p>
<p class="TitolCondicions">${_(u"8. INFORMACIÓ BÀSICA SOBRE PROTECCIÓ DE DADES")}</p>  
<p class="sagnia">${_(u"8.1 S’informa a la persona sòcia que el responsable de dades personals facilitades en el marc d’aquestes condicions és SOM ENERGIA, SCCL, que els ha d’emprar únicament per atendre les sol·licituds, realitzar comunicacions informatives i enviar comunicacions comercials sobre els productes i/o serveis de SOM ENERGIA, SCCL, i en particular sobre la relació amb la persona sòcia de la cooperativa. La legitimació per a aquest tractament deriva de l’execució de les presents condicions, així com del consentiment que la contractant va expressar en fer-se sòcia de SOM ENERGIA, SCCL. Les dades es conservaran mentre es mantingui la relació societària, i en el seu cas, durant els anys necessaris per complir amb les obligacions legals.")}</p> 

<p class="sagnia">${_(u"8.2 En el marc de l’execució d’aquestes condicions està prevista la cessió de dades, procedents de la mateixa persona interessada, a terceres empreses quan sigui necessari per a la prestació dels serveis contractats, tals com, per exemple, assessories fiscals i comptables, bancs i caixes, administració tributària o altres administracions públiques, etc.")}</p>

<p class="sagnia">${_(u"8.3 La contractant té dret a accedir, rectificar i suprimir les dades, així com altres drets, indicats en la informació addicional que figura a la política de privacitat de SOM ENERGIA, SCCL, disponible al seu espai web d’internet www.somenergia.coop, i que pot exercir els drets o trobar la informació addicional dirigint-se al responsable de tractament de les seves dades de SOM ENERGIA, SCCL:")}</p> 

<ul class="punts">
<li>${_(u"Per correu postal dirigit a l’adreça:<br>C/ Riu Güell, 68 17005 Girona.")}</li>
  <li>${_(u"Per correu electrònic dirigit a gdpr@somenergia.coop")}</li>
  <li>${_(u"Per telèfon al número gratuït: 900 103 605 o bé al 872 202 550")}</li>
</ul>
<p class="TitolCondicions">${_(u"9. CLÀUSULES MISCEL·LÀNIA")}</p>
<p class="sagnia">${_(u"9.1 Amb l'acceptació d'aquestes condicions, la persona sòcia declara conèixer i acceptar que la finalitat d’aquestes condicions no és, en cap cas, oferir per part de la cooperativa a favor del soci/a un producte financer, ni garantir-li rendibilitat financera, sinó permetre desenvolupar l’objecte social definit en els estatuts socials de Som Energia, SCCL.")}</p>

<p class="sagnia">${_(u"9.2 La notificació al soci/sòcia de les operacions i comunicacions de caràcter general derivades de l’operativa d’aquestes aportacions voluntàries, es realitzaran prioritàriament per correu electrònic a l’adreça indicada en aquestes condicions. És responsabilitat de la persona sòcia el manteniment correcte, en estat operatiu, del correu referit.")}</p>

<p class="sagnia">${_(u"9.3 En cas d’incompatibilitat, les disposicions establertes als Estatuts socials vigents i als acords de l'Assemblea general prevaldran sobre les presents condicions. La declaració de qualsevol d’aquestes condicions com a invàlida o ineficaç no afectarà la validesa o eficàcia de la resta, que continuarà essent vinculant per a la persona sòcia i la cooperativa, les quals es comprometen en aquest cas a substituir la clàusula afectada per una altra de vàlida d’efecte equivalent, segons els principis de bona fe i equilibri de contraprestacions.")}</p> 

<p class="sagnia">${_(u"9.4 Aquest contracte es regirà i interpretarà en tots els seus extrems per les lleis espanyoles que resultin aplicables.")}</p>

<p class="sagnia">${_(u"9.5 Totes les controvèrsies que puguin sorgir en relació amb aquest contracte se sotmetran a la jurisdicció dels jutjats i tribunals de la ciutat de Girona, excepte en aquells supòsits que es disposi una altra cosa de forma imperativa per la normativa aplicable a l’efecte.")}</p>
<div class="final"></div>
</div>
%endfor
</body>
</html>