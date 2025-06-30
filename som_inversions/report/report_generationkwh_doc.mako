<%
from datetime import datetime, date
from math import ceil

%>
<!doctype html>
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<head>
    <style type="text/css">
    ${css}
    body {
        font-family: helvetica;
        font-size: 14px;
        padding: 10px;
    }

    img.logo {
        float: right;
    }

     div.contracte {
         clear: both;
         margin: 30px;
    }

    h1 {
        font-size: large;
        text-align: center;
        page-break-before: avoid;
    }

    h2, .h2_format {
        font-size: medium;
        text-decoration: underline;
        font-weight: bold;
    }

    h3 {
        font-size: medium;
        text-decoration: underline;
    }

    p {
        padding: 8px;
    }

    div.signatures_block {
        page-break-inside: avoid;
        padding: 0px;
        margin: 0px;
    }

    div.signatures {
        align: center;
        width: 100%;
        page-break-inside: avoid;
    }

    div.signatura {
        float: left;
        page-break-inside: avoid;
    }

    ul {
        list-style-type: none;
        padding: 0px;
        margin-left: 5em;
    }

     li.image {
         height: 150px;
         width: 150px;
     }

     li.signature_text {
         height: 90px;
         width: 150px;
         margin-top: 60px;
         margin-bottom: 0px;
         font-size: xx-small;
     }

     div.contracte_llarg {
         margin-left: 30px;
     }

     div.contracte_llarg h2 {
         text-decoration: none;
         display: inline;
         margin: 30px 0px;
     }

    ol {
        counter-reset: item;
        display: table;
        margin: 0px;
        padding: 10px;
    }

    ol li {
        display: table-row;
        border-spacing: 10px;
        font-size: medium;
    }

    ol li::before {
        display: table-cell;
        padding-right: 5px;
        content: counters(item, ".") ". ";
        counter-increment: item;
        font-weight: bold;
    }

    div.annex1, div.annex2  {
        margin-left: 30px;
        font-size: medium;
    }

/* ANNEX */
    table {
        border-collapse: collapse;
        font-size: medium;
        width: 100%;
        page-break-inside: avoid;
    }

    th {
        background-color: lightgrey;
        font-weight: bold;
    }

    table, td, th{
        border: 1px solid black;
        text-align: left;
    }

    table.annex1_table caption {
        padding: 5px 0px;
        text-align: left;
    }

    table.annex2_table {
        border: 0px;
        text-align: left;
        page-break-inside: avoid;
    }

    table.annex2_table caption {
        text-align: left;
    }

    table.annex2_table td, table.annex2_table tr{
        border: 0px;
        text-align: left;
    }

    table.annex2_table td {
        width: 50px;
    }

    .big_sum {
        font-size: xx-large;
    }

     p.math {
         border: 1px solid black;
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
    <h3>${_(u'Data del contracte:')}</h3>
    <p class="data">${contract_date.day} de ${month_names[contract_date.month-1]} de ${contract_date.year}</p>
    <p>${_("Aquest contracte només serà actiu un cop el pagament corresponent s'hagi fet efectiu")}</p>

    <div class="signatures">
        <div class="signatura">
            <ul>
                <li><b>Som Energia, SCCL</b></li>
                <li><img src="${addons_path}/som_inversions/report/firma_cb.png" height="150" width="200"/></li>
                <li><b>${_(u'Signat:')} Carles Barbarà Puig</b></li>
            </ul>
        </div>
        <div class="signatura">
            <ul>
                <li><b>${_(u'El Soci/La Sòcia')}</b></li>
                <li class="signature_text">${_('Condicions acceptades a través del formulari web el dia %s') % creation_date_str}</li>
                <li><b>${_(u'Signat:')} ${inv.partner_id.name or ''}</b></li>
            </ul>
        </div>
    </div>
</div>
</%def>
<div>
    <img class="logo" src="${addons_path}/som_inversions/report/logo2.jpg" width="150" height="150"/>
</div>
<div class="contracte">
    <h1>${_(u'CONTRACTE D’ADHESIÓ AL SISTEMA D’AUTOPRODUCCIÓ COL·LECTIVA D’ENERGIA ELÈCTRICA PROVINENT DE FONTS RENOVABLES')}</h1>

    <h2>${_(u'CONDICIONS PARTICULARS')}</h2>
    <h3>${_(u'Parts contractants:')}</h3>

    <p>${inv.partner_id.name or ''}${_(u', en endavant, el <b>Soci/Sòcia</b>.')}</p>
    <p>${_(u'SOM ENERGIA, S.C.C.L., amb domicili a carrer Pic de Peguera, 15, Parc Científic i Tecnològic de la UdG, 17003 - Girona i amb NIF F55091367.')}</p>


    <h3>${_(u'Nombre d’Accions Energètiques del Soci en el Sistema d’Autoproducció Col·lectiva:')}</h3>

    <p>${int(ceil(amount / 100) or 1)}${_(u' Accions Energètiques. Cada Acció Energètica correspon a un préstec per part del Soci/Sòcia de 100 €.')}</p>

    <h3>${_(u'Nombre de kWh per Acció Energètica')}</h3>

    <p>${_(u'El nombre de kWh que pertocaran a cada Acció Energètica s’establirà  en funció de la producció real de les Plantes Associades al sistema Generation kWh d’acord amb els criteris establerts a les Condicions Generals i els seus annexos.')}</p>

    <p><span class="h2_format">${_(u'Import del préstec concedit pel Soci/Sòcia a Som Energia')}</span>, ${int(amount)} € (${int(ceil(amount / 100) or 1)} ${_(u' Accions Energètiques x 100 €)')}</p>

    <h3>${_(u'Condicions de retorn del préstec:')}</h3>

    <p>${_(u'El capital aportat es retornarà un cop a l’any repartida en 23 pagues iguals i una última paga del doble de les anteriors . La primera quota de retorn del préstec es farà efectiva dos anys després de l’acceptació d’aquestes condicions particulars.')}</p>

    ${signatures(inv)}
</div>
<p style="page-break-after:always"></p>
<div class="contracte_llarg">
<h1>${_(u'Condicions generals del contracte d’adhesió al sistema d’autoproducció col·lectiva d’energia elèctrica provinent de fonts renovables')}</h1>

<ol>
    <li><h2>${_(u'OBJECTE')}</h2>
        <ol>
            <li>${_(u'L’objecte del present contracte (el <b>“contracte”</b> o el <b>“contracte d’autoproducció col·lectiva”</b>) és regular la inclusió del soci o sòcia sotasignat (el <b>“soci/a”</b>) en el sistema d’autoproducció d’energia elèctrica de fonts renovables (d’ara endavant, el <b>“sistema d’autoproducció col·lectiva”</b>) que Som Energia, SCCL, (d’ara endavant, “Som Energia”) ha decidit impulsar i posar en pràctica i, en concret, en la Cartera de projectes del referit sistema d’autoproducció col·lectiva, acordada per l’Assemblea general de Som Energia celebrada el dia 09/05/2015 (enllaç a l’acta). En la referida assemblea es va acordar, com a objecte de la indicada Cartera de projectes, emprendre inversions per a la construcció i posada en marxa de plantes de producció d’energia elèctrica de fonts renovables i, per tant, sol·licitar a les persones sòcies que volguessin incloure’s en el sistema esmentat, l’aportació, via préstec gratuït (en els termes que es detallen a continuació), dels recursos indicats, amb subjecció a les condicions que s’establiran en aquest contracte. El soci/a declara haver rebut còpia de l’acord adoptat per l’Assemblea general esmentada. El present contracte es convé en el marc i amb submissió als valors i principis cooperatius.')}</li>
            <li>${_(u'L’objectiu a assolir, en virtut del conjunt de contractes d’autoproducció col·lectiva, és facilitar que les persones sòcies que els subscriguin puguin passar a consumir, mitjançant la seva agrupació, una energia elèctrica equivalent a la que produeixi la mateixa Som Energia, procedent de fonts renovables, mitjançant les plantes de producció que, amb el suport financer obtingut de tals contractes, promourà a tal fi, salvant així els inconvenients actuals que afecten l’autoproducció individual d’aquest tipus d’energia elèctrica i la retirada d’incentius als projectes de producció d’energies renovables. A aquests efectes, l’accés a aquest sistema d’autoproducció col·lectiva s’entén com una opció del soci/a d’utilitzar electricitat al preu resultant dels costos de generació de les plantes associades. Per contractar i mantenir la titularitat dels drets derivats del present contracte cal tenir, en tot moment, la condició de soci/a de Som Energia i ser titular d’un contracte de subministrament d’energia elèctrica subscrit amb Som Energia. Per tant, en aquest contracte es regularà el règim aplicable en el supòsit que el soci/a deixi de complir tals condicions. En supòsits excepcionals, en els quals hi hagi una relació prèvia acreditable entre un soci/a i un no soci/a titular del contracte de subministrament d’energia elèctrica subscrit amb Som Energia (relació de parentiu, arrendador-arrendatari, copropietaris, etc.), Som Energia permetrà que el no soci/a titular del contracte de subministrament d’energia elèctrica participi en el sistema d’autoproducció col·lectiva sempre que sigui el soci/a qui tingui i mantingui la condició de prestador o prestadora de Som Energia. En aquests casos, la persona titular del contracte de subministrament elèctric haurà d’acceptar les condicions generals i particulars objecte d’aquest contracte juntament amb el soci/a.')}</li>
            <li>${_(u'En el present contracte es regulen les condicions de l’aportació que, per adherir-se al sistema d’autoproducció col·lectiva, el soci/a fa a Som Energia en concepte de préstec gratuït, per l’import que consta a les condicions particulars i, per tant, el procediment mitjançant el qual Som Energia, durant el període de vigència del present Contracte, restituirà al soci/a la suma prestada. L’aportació del préstec permetrà a Som Energia finançar les plantes de producció de fonts d’energies renovables vinculades a aquest contracte. La qualificació del préstec com a gratuït es refereix a la inexistència d’interessos o remuneració del capital, en els termes i condicions que s’estableixen en el present Contracte. Ho és sense perjudici del potencial estalvi que pugui resultar en un concret exercici com a conseqüència de l’existència d’una diferència positiva, que resulti daplicar el Preu Generation kWh (segons definit en l’Annex II) respecte de la tarifa general aplicada per Som energia a la resta de contractes de subministrament d’energia elèctrica.')}</li>
            <li>${_(u'No obstant això, en cas que durant la vigència d’aquest contracte hi hagi canvis en el règim retributiu que impliquin millores per als projectes d’energies renovables en general (possibilitat d’incorporació d’alguns projectes, o tots, al règim retributiu específic, etc.) o per als projectes de les plantes associades en particular (recepció d’alguna subvenció i/o ajuda específica, etc.), l’Assemblea general, a proposta del Consell Rector, podrà aprovar la retribució d’un interès a determinar a favor del soci/a prestamista sempre que no es perjudiqui la viabilitat general de la cartera de projectes. La resolució de l’Assemblea general establirà les condicions, termini i modes de pagament concretes, que produiran efecte des de l’acceptació per part del soci/a aquestes condicions més avantatjoses.')}</li>
            <li>${_(u'El contracte d’autoproducció col·lectiva i el préstec convingut en aquest marc tenen caràcter personal i només podran ésser cedits a favor de les persones sòcies que compleixin les condicions indicades a l’apartat 1.2 anterior i amb l’aprovació prèvia i documentada de Som Energia, tal com es regula en el present contracte. Tot això sens perjudici de l’eventual cancel·lació del present contracte que, en els termes que s’hi convenen, es pugui acordar o convenir en el seu moment.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'DURADA I ENTRADA EN VIGOR')}</h2>
        <ol>
            <li>${_(u'El present contracte es convé per un termini de VINT-I-CINC (25) ANYS, període en el qual Som Energia haurà de retornar en la seva totalitat l’import del préstec rebut d’acord amb els terminis, forma de pagament i imports detallats a les condicions particulars, sens perjudici del que s’indica a les condicions generals 6 i 7.2.')}</li>
            <li>${_(u'El present contracte entrarà en vigor en el moment que hagi quedat subscrit pel soci/a i per Som Energia i hagi resultat efectiu l’ingrés per part del soci/a de l’import del préstec que consta a les condicions particulars.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'PLANTES DE PRODUCCIÓ D’ENERGIA ELÈCTRICA ASSOCIADES A AQUEST CONTRACTE')}</h2>
        <ol>
            <li>${_(u'Les sumes prestades per les persones sòcies es destinaran a finançar la construcció i posada en marxa dels projectes de plantes de producció d’energia elèctrica renovable. Aquestes plantes de producció (d’ara endavant, les <b>“plantes associades”</b>) queden, doncs, vinculades o associades als contractes d’autoproducció col·lectiva i, per tant, el cost de l’electricitat generada per les plantes associades servirà com a paràmetre per calcular les tarifes en la facturació dels contractes de subministrament dels socis i sòcies acollits, mitjançant la subscripció del present contracte, a la cartera de projectes.')}</li>
            <li>${_(u'No obstant l’anterior, l’Assemblea general de Som Energia podrà associar a la present cartera de projectes altres plantes de producció d’energia elèctrica promogudes per Som Energia a l’empara d’altres campanyes, que en tal cas podran passar també a ser plantes associades de l’actual cartera de projectes. I també, viceversa, l’Assemblea de Som Energia podrà associar a altres carteres les plantes associades a aquesta. Per tant, en els casos aquí previstos, les plantes associades serviran de referència comuna per a la determinació del preu <i>generation</i> kWh.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'PRÉSTEC DEL SOCI/A')}</h2>
        <ol>
            <li>${_(u'El soci/a, amb la finalitat referida a la condició general 1, lliura a Som Energia, en concepte de préstec gratuït (en els termes descrits a la condició general 1.3), l’import que consta en les condicions particulars i que aquesta declara rebre i destinarà a finançar la construcció de les plantes associades.')}</li>
            <li>${_(u'Som Energia queda obligada a retornar al soci/a el capital del referit préstec en el termini màxim de vint-i-cinc (25) anys de vigència del present contracte d’acord amb els terminis, forma de pagament i imports establerts a les condicions particulars. Les parts acorden que d’aquest capital es compensaran les quantitats que Som Energia hagi ingressat a l’Agència Tributària per compte del soci/a en concepte de retenció a compte de l’Impost sobre la renda de les persones físiques, segons el que preveu la clàusula 5.5.')}</li>
            <li>${_(u'El preu <i>Generation kWh</i> a aplicar es calcularà, segons s’indica en la condició general 5 següent, en funció del cost de generar l’electricitat a les plantes associades. Per tant, atès que existirà una fase de construcció de les plantes associades a construir en virtut de la present cartera de projectes, dins de la qual es convé aquest contracte, s’estableix un període de carència inicial, durant el qual no es retornarà el préstec ni s’aplicarà el preu <i>Generation kWh</i>. L’indicat període de carència té una durada d’un (1) any. No obstant això, si es produís un endarreriment en la construcció i posada en marxa de les plantes associades a construir, en virtut de la cartera de projectes vigent, l’Assemblea general de Som Energia podrà prorrogar aquest període de carència fins que les referides plantes associades estiguin plenament operatives. Tal pròrroga no podrà superar el termini addicional de sis (6) mesos, transcorregut el qual, si continués la situació indicada, Som Energia, per acord de la seva Assemblea general, proposarà al soci/a, alternativament i a la seva elecció, o bé una adaptació del present contracte, o bé la devolució del préstec i la cancel·lació del contracte, en un termini addicional de sis (6) mesos.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'LA FACTURACIÓ DEL CONTRACTE DE SUBMINISTRAMENT: ACCIONS ENERGÈTIQUES I PREU GENERATION KWH')}</h2>
        <ol>
            <li>${_(u'La participació del soci/a o, excepcionalment del titular del contracte no soci/a segons l’establert a la clàusula 1.2, en el sistema d’autoproducció col·lectiva objecte d’aquest contracte li atorga un nombre determinat d’accions energètiques en funció de l’import del préstec concedit. El preu <i>Generation kWh</i> s’aplicarà exclusivament a la quantitat d’electricitat que li pertoqui al soci/a en funció de les accions energètiques assignades.')}</li>
            <li>${_(u'Cada acció energètica (100 €) equival a una quantitat d’energia elèctrica (kWh) determinada en funció de la producció real de les plantes associades. A l’annex I d’aquestes condicions generals s’estableixen els criteris a partir dels quals es determinaran i ajustaran les referides ràtios per a cada un dels períodes tarifaris.')}</li>
            <li>${_(u'Cada acció energètica (de 100 €) equival a la quantitat d’energia elèctrica (kWh) en funció de la producció real de les plantes segons el que consta a les condicions particulars. En l’annex II d’aquestes condicions generals s’estableixen els criteris a partir dels quals es determinaran i ajustaran les referides ràtios per a cada un dels períodes tarifaris.')}</li>
            <li>${_(u'El Consell Rector aprovarà, per a cada anualitat, d’acord amb les directrius de l’Assemblea general, el preu <i>Generation kWh</i> corresponent en funció dels costos d’obtenció, per Som Energia, de l’energia elèctrica produïda per les plantes associades. Els annexos I i II d’aquestes condicions generals desglossen els costos o despeses i el mètode de càlcul que Som Energia prendrà en consideració per a la determinació del preu <i>Generation kWh</i>.')}</li>
            <li>${_(u'El Preu Generation kWh de cada anualitat s’aprovarà amb caràcter definitiu pel Consell Rector de Som Energia i tindrà efectes en data 31 de desembre de cada anualitat. Així, fins a aquesta data s’aplicarà amb caràcter merament provisional el Preu Generation kWh, la qual cosa pot implicar la regularització del Preu ja aplicat a l’electricitat que li correspongui al soci en el transcurs de l’anualitat si aquest diferís del definitiu. En els 30 dies següents s’informarà al soci del resultat d’aplicar el Preu Generation kWh en l’exercici fiscal anterior (de gener a desembre), realitzant la corresponent retenció a compte de l’Impost sobre la Renda de les Persones Físiques.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'RETORN ANTICIPAT DEL PRÉSTEC')}</h2>
        <ol>
            <li>${_(u'L’exercici, per part del soci/a o per part de Som Energia, de l’opció de retorn anticipat del préstec haurà de ser comunicat per la part optant a l’altra part amb una anticipació mínima de 90 dies. En aquest cas, el present contracte quedarà cancel·lat i l’import pendent d’amortització en aquella data del préstec concedit per part del soci/a a favor de Som Energia haurà de ser retornat per aquesta última a aquell. Aquesta devolució es produirà en el termini de 90 dies a partir de la data d’efectiva resolució del contracte. No obstant això, en el supòsit que el conjunt de préstecs derivats de contractes d’autoproducció col·lectiva a retornar anticipadament, en el curs d’una anualitat, superi el 5 % de l’import global pendent de la seva amortització, Som Energia podrà ajornar fins a l’anualitat següent la devolució d’aquells préstecs que superin el límit. En tal cas, la devolució es produiria dins dels primers 3 mesos de l’anualitat següent (a la qual li seria igualment d’aplicació el límit indicat màxim de devolucions exigibles). La referida cancel·lació anticipada del contracte comportarà la meritació d’un càrrec a favor de Som Energia per despeses de gestió corresponent com a màxim al 4 % de l’import del préstec pendent d’amortitzar en el moment de la devolució. En conseqüència, el soci/a deixarà de participar des d’aquell moment en el sistema d’autoproducció col·lectiva.')}</li>
            <li>${_(u'Atès que la titularitat del present contracte, per part del soci/a, està sempre condicionada al fet que tingui i mantingui la seva condició de soci/a de Som Energia i de titular d’un contracte de subministrament amb aquesta, en el supòsit que, de forma sobrevinguda, el soci/a deixés de complir algun d’aquests requisits i no tingués acordada i aprovada la cessió del contracte en els termes establerts a l’apartat 7.1, el present contracte quedarà cancel·lat i l’import pendent d’amortització en aquella data del préstec concedit per part del soci/a a favor de Som Energia haurà de ser retornat per aquesta última a aquell amb els límits indicats en aquesta clàusula. Aquesta clàusula també serà aplicable quan, de forma excepcional, el titular del contracte no soci/a vinculat a un soci/a d’acord amb el que estableix la clàusula 1.2 deixi de complir aquest requisit de titularitat del contracte de subministrament elèctric. En aquest cas, el préstec concedit per part del soci/a a favor de Som Energia haurà de ser retornat per aquesta última al soci/a d’acord amb els límits establerts en aquesta clàusula i el titular del contracte no soci/a deixarà de participar des d’aquell moment en el sistema d’autoproducció col·lectiva.')}</li>
            <li>${_(u'No obstant això, en els casos de canvi de domicili, s’acostuma a produir un lapse de temps en el qual la persona titular del contracte de subministrament elèctric ha de fer els tràmits necessaris per regularitzar el contracte amb Som Energia al nou domicili. En aquests casos, sempre que la persona titular notifiqui de forma fefaent a Som Energia la intenció de regularitzar el contracte amb Som Energia al nou domicili i el període de temps per realitzar el canvi de titularitat no superi l’any de durada des de la baixa de l’anterior contracte, no s’aplicarà l’establert a la clàusula 6.2 i el préstec es continuarà ajustant als terminis i modes de pagament previstos a les condicions particulars sense que se’n produeixi el retorn anticipat. Ara bé, durant aquest període el soci/a no tindrà accés al preu <i>Generation kWh</i> ni podrà reclamar posteriorment cap import addicional per aquest concepte.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'CANVI DE TITULARITAT DEL CONTRACTE')}</h2>
        <ol>
            <li>${_(u'El soci/a, amb el consentiment previ i escrit de Som Energia, podrà cedir el present contracte a favor d’un altre soci/a, que compleixi també el requisit de ser titular d’un contracte de subministrament i per al qual les accions energètiques objecte del present contracte siguin adequades al seu nivell previsible de consum elèctric. La cessió comportarà, en tal cas, la subrogació del soci/a adquirent en la posició jurídica del cedent en aquest contracte. Serà a càrrec de l’adquirent pagar al cedent la suma que ambdues parts convinguin per rescabalar al cedent les sumes del préstec que tingui pendents de recuperar. Som Energia, en tals supòsits facilitarà a les dues parts informació actualitzada sobre la suma pendent d’amortització del préstec.')}</li>
            <li>${_(u'En cas de mort del soci/a titular del contracte, el seu successor/a (un cop acreditat documentalment aquesta condició davant de Som Energia) podrà optar per exercir el dret a retorn anticipat del préstec i consegüent cancel·lació del contracte o optar per subrogar-se en els drets i deures del difunt/a i tenir accés al sistema d’autoproducció col·lectiva. Si exerceix aquesta darrera opció, el successor/a haurà de ser titular d’un contracte de subministrament elèctric amb Som Energia o realitzar i formalitzar els tràmits pertinents a aquests efectes.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'DECLARACIONS DEL SOCI/A')}</h2>
        <ol>
            <li>${_(u'Amb l’acceptació d’aquest contracte, el soci/a declara conèixer i acceptar que aquest és un contracte de tipus col·laboratiu, en el marc de la seva pertinença a Som Energia, i que la seva finalitat no és, en cap cas, oferir per part de Som Energia a favor del soci/a un producte financer o d’estalvi, ni garantir-li rendibilitat financer pel préstec el qual, en el marc del contracte, el soci/a concedeix a Som Energia.')}</li>
            <li>${_(u'Amb l’acceptació del present contracte, el soci/a manifesta que la finalitat per ell perseguida és la possibilitat d’assegurar, mitjançant la seva actuació concertada i agrupada amb altres persones sòcies, que una part substancial de l’energia elèctrica que consumeix sigui equivalent a l’energia elèctrica provinent de fonts renovables, produïda per les plantes associades promogudes i operades per Som Energia; i que el préstec concedit a Som Energia és un mitjà o instrument per assolir tal objectiu col·laboratiu i de sostenibilitat mediambiental.')}</li>
            <li>${_(u'Amb l’acceptació del present contracte,  el soci/a i/o titular del contracte de subministrament elèctric manifesta conèixer i acceptar que la determinació del preu Generation kWh al qual tindrà accés es durà a terme en funció dels paràmetres establerts a l’annex II d’aquest contracte i serà de caràcter variable.')}</li>
            <li>${_(u'La determinació i quantificació periòdica dels paràmetres referits, mitjançant l’aplicació dels criteris establerts als annexos I i II d’aquestes condicions generals, és facultat, segons el present contracte, de l’Assemblea general de persones sòcies de Som Energia, de la qual el soci/a forma part, sens perjudici de les actuacions puntuals del Consell Rector, referides en aquest contracte, sotmeses al control i ratificació de l’Assemblea general esmentada, extrems aquests que el soci/a declara conèixer i accepta.')}</li>
            <li>${_(u'Amb l’acceptació del present contracte, el soci/a manifesta conèixer i acceptar que el préstec per ell concedit és de caràcter gratuït i que no resultarà retribuït, sense perjudici del que és relatiu a l’aplicació del preu Generation kWh i llevat que es produeixi alguna de les condicions previstes a 1.4. A aquests efectes, l’accés a aquest sistema d’autoproducció col·lectiva s’entén com una opció del soci/a d’utilitzar electricitat al preu resultant dels costos de generació de les plantes associades, sense que en cap cas impliqui una contraprestació o retribució pel préstec concedit.')}</li>
            <li>${_(u'Amb l’acceptació del present contracte, tant el soci/a com la persona titular del contracte de subministrament d’energia elèctrica, en els casos que no siguin la mateixa persona d’acord amb els supòsits previstos a la clàusula 1.2, manifesten i accepten que l’accés a la participació en el sistema d’autoproducció col·lectiva per part de la persona titular del contracte de subministrament d’energia elèctrica no s’entén en cap cas com la transmissió d’un valor net de béns i/o drets adquirits per part del soci/a, sinó com una opció exercida de forma conjunta per facilitar que una part de l’energia elèctrica consumida sigui equivalent a l’energia elèctrica provinent de fonts renovables que es produirà a les plantes associades promogudes i operades, directament o indirecta, per Som Energia. En tot cas, les declaracions i retencions a compte de l’Impost sobre la Renda de les Persones Físiques (IRPF) que Som Energia hagi de realitzar en compliment de la normativa aplicable en cada moment s’efectuarà en relació al Soci prestador, en constituir l’estalvi resultant de l’aplicació del Preu Generation kWh (en els casos en què existeixi una diferència positiva respecte a la tarifa general aplicada per Som energia a la resta de contractes de subministrament d’energia elèctrica), un estalvi vinculat al préstec realitzat per aquest Soci.')}</li>
            <li>${_(u'Amb l’acceptació del present contracte el soci/a i/o titular del contracte de subministrament elèctric manifesta conèixer que el sistema d’autoproducció col·lectiva incidirà de forma exclusiva en el concepte d’energia del terme variable de la factura i que aquest contracte no exclou al soci/a de pagar els altres conceptes d’aquest terme (peatges, pagaments regularitzats, taxes, etc.)')}</li>
        </ol>
    </li>
    <li><h2>${_(u'DECLARACIONS DE SOM ENERGIA')}</h2>
        <ol>
            <li>${_(u'Som Energia garanteix al soci/a la devolució, en el termini màxim de vint-i-cinc (25) anys, del capital del préstec concedit en el marc d’aquest contracte d’acord amb els terminis, modes de pagament i imports detallats a les condicions particulars.')}</li>
            <li>${_(u'Som Energia garanteix al soci/a que la determinació del preu Generation kWh es durà a terme, per part del Consell Rector, en aplicació dels criteris aprovats per l’Assemblea general, en funció estrictament dels costos reals, per a la cooperativa, de l’energia elèctrica produïda per les plantes associades, més, únicament, un import adequat i proporcional destinat a la cobertura dels costos generals de la cooperativa i despeses de gestió, i amb aplicació dels criteris que consten a l’annex II d’aquestes condicions generals.')}</li>
            <li>${_(u'Som Energia mantindrà informat el soci/a, tant en el marc de l’Assemblea general com mitjançant la informació escrita que, com a mínim amb caràcter anual, li facilitarà, de l’evolució de les plantes associades, del seu procés de construcció i, posteriorment, d’operació, i dels costos per a la cooperativa de l’energia produïda per aquestes.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'NATURALESA JURÍDICA DEL PRÉSTEC CONCEDIT EN EL MARC DEL CONTRACTE')}</h2>
        <ol>
            <li>${_(u'El préstec concedit pel soci/a es regeix per la normativa pròpia per a aquests contractes establerta pel Codi civil i pel Codi de comerç. Som Energia està obligada a retornar al soci/a la totalitat de la suma prestada en el termini convingut, amb deducció prèvia dels imports avançats per Som Energia a l’Agència Tributària motivats pel mateix contracte. El soci/a, en tant que prestador, no participa en les eventuals pèrdues dels negocis o activitats als quals es destinaran les sumes prestades i, per tant, el present contracte no té la consideració jurídica de compte en participació.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'DADES DE CARÀCTER PERSONAL')}</h2>
        <ol>
            <li>${_(u'El responsable de les dades personals facilitades en el marc del contracte actual és Som Energia, SCCL, qui els emprarà únicament per a l’objecte i finalitat previstos en quest, així com l’enviament de comunicacions sobre els seus productes i serveis. La legitimació per a aquest tractament deriva de l’execució del contracte actual, així com del consentiment que el soci/a expressa en subscriure’l.')}</li>
            <li>${_(u'En el marc de l’execució d’aquest contracte està prevista la cessió de dades, procedents de la mateixa persona interessada, a terceres empreses quan sigui necessari per a la seva execució, tal com, per exemple, assessories fiscals i comptables, bancs i caixes, administració tributària o altres administracions públiques i tercers països.')}</li>
            <li>${_(u'El soci/a té dret a accedir, rectificar i suprimir les dades, així com altres drets, indicats en la informació addicional que figura en la Política de Privacitat de Som Energia, SCCL, disponible en la seva pàgina en Internet www.somenergia.coop i que pot exercir els drets o trobar la informació addicional dirigint-se a l’adreça de Som Energia, SCCL, tal com indica la condició general 12.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'MODIFICACIÓ')}</h2>
        <ol>
            <li>${_(u'Les parts estan obligades al compliment de les obligacions reflectides en el contracte conforme als termes que s’hi recullen.')}</li>
            <li>${_(u'Sense perjudici de l’anterior, el contracte actual podrà ser modificat per Som Energia, SCCL, per decisió del seu Consell Rector o de l’Assemblea general. Tota modificació serà degudament comunicada al soci/a de conformitat amb el que es preveu en aquesta clàusula, i podrà ser motivada a fi de complir amb la normativa del mercat elèctric, així com per a la fixació de criteris sobre els valors que la cooperativa desitja transmetre.')}</li>
            <li>${_(u'Igualment, Som Energia, SCCL, podrà modificar unilateralment el contracte en el cas que demostri que, per alteracions de la normativa aplicable o qualsevol altra circumstància equivalent (per exemple, alteracions del mercat de producció o comercialització d’energia), fos necessària aquesta modificació per ajustar el contingut del contracte a la normativa vigent o quan el compliment de les prestacions contractuals li resulti excessivament onerós.')}</li>
            <li>${_(u'Aquestes modificacions seran comunicades al soci/a amb una antelació de trenta (30) dies naturals a l’aplicació de la modificació i, en cas que suposin un perjudici per al soci/a, aquest podrà resoldre el contracte comunicant-lo a Som Energia, SCCL, per qualsevol dels mitjans establerts en el contracte actual en el termini de quinze (15) dies naturals següents a aquesta comunicació. En cas de no resoldre el contracte en aquest termini, la modificació s’entendrà acceptada pel soci/a.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'NOTIFICACIONS I ALTRES')}</h2>
        <ol>
            <li>${_(u'La notificació al soci/a de les operacions, liquidacions, facturacions i comunicacions de caràcter general derivades de l’operativa d’aquest contracte i, en especial, del préstec concedit en aquest marc, es realitzaran prioritàriament per correu electrònic a l’adreça indicada a les condicions particulars. És responsabilitat del soci/a el manteniment correcte, en estat operatiu, del correu referit.')}</li>
            <li>${_(u'Excepte en els casos indicats en l’anterior apartat 12.1, qualsevol notificació que hagi de practicar una part a l’altra en relació amb el present Contracte, es durà a terme per correu certificat amb justificant de recepció, o per un altre mitjà equivalent que permeti deixar constància del seu enviament, recepció i contingut.')}</li>
            <li>${_(u'La declaració de qualsevol d’aquestes condicions generals com a invàlida o ineficaç no afectarà la validesa o eficàcia de la resta, que continuarà essent vinculant per a les parts contractuals, les quals es comprometen en aquest cas a substituir la clàusula afectada per una altra de vàlida d’efecte equivalent, segons els principis de bona fe i equilibri de contraprestacions. La renúncia per qualsevol de les parts a exigir en un moment determinat el compliment de qualsevol de les condicions generals aquí estipulades no implicarà una renúncia amb caràcter general ni crearà un dret adquirit per l’altra part.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'LEGISLACIÓ I JURISDICCIÓ')}</h2>
        <ol>
            <li>${_(u'Aquest contracte es regirà i interpretarà en tots els seus extrems per les lleis espanyoles que resultin aplicables.')}</li>
            <li>${_(u'Totes les controvèrsies que puguin sorgir en relació amb aquest contracte se sotmetran a la jurisdicció dels jutjats i tribunals de la ciutat de Girona, excepte en aquells supòsits que es disposi una altra cosa de forma imperativa per la normativa aplicable a l’efecte.')}</li>
        </ol>
    </li>
    <li><h2>${_(u'CONTRACTE COMPLET')}</h2>
        <ol>
            <li>${_(u'Aquestes condicions generals, juntament amb les condicions particulars, constitueixen la integritat dels pactes existents entre les parts en relació amb els extrems que en constitueixen el seu objecte, substituint qualssevol altres pactes o acords al respecte existents entre les parts amb anterioritat a la seva subscripció.')}</li>
        </ol>
    </li>
</ol>
    ${signatures(inv)}
</div>
<p style="page-break-after:always"></p>
<div class="annex1">
<h1>${_(u'ANNEX I')}</h1>
<h1>${_(u'CRITERIS A APLICAR PER LA DETERMINACIÓ DEL PREU GENERATION KWH')}</h1>
<p>${_(u'L’assignació de kWhs a cada Acció Energètica es realitzarà en funció de la <b>producció real</b> que tinguin les plantes. Diàriament es realitzarà el recompte de quina ha estat aquesta producció i a partir d’aquesta informació es reflectirà a la factura elèctrica <b>segons s’estableix a l’ Annex II.</b>')}</p>
<p><h3>${_(u'1) Establiment del preu de cost mitjà de generació Generation kWh.')}</h3></p>
<p>${_(u'Per tal de mostrar quin serà el criteri a seguir a l’hora de determinar el preu de cost mitjà de generació fem una simulació amb tres exemples de projectes tipus.')}</p>

<table class="annex1_table">
    <caption><h2>${_(u'Projecte 1:')}</h2></caption>
    <tr><th>${_(u'Tipologia')}</th><td>${_(u'Projecte FV sobre terreny')}</td></tr>
    <tr><th>${_(u'Inversió prevista')}</th><td>${_(u'1.800.000 €')}</td></tr>
    <tr><th>${_(u'Producció anual prevista')}</th><td>${_(u'2.818.580 kWh')}</td></tr>
    <tr><th>${_(u'Vida útil considerada')}</th><td>${_(u'30 anys')}</td></tr>
    <tr><th>${_(u'Període d’amortització')}</th><td>${_(u'25 anys')}</td></tr>
    <tr><th>${_(u'Valor residual considerat als 25 anys')}</th><td>${_(u'416.666 €')}</td></tr>
    <tr><th>${_(u'Cost d’amortització (1):')}</th><td>${_(u'0.020 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost O&M (operació i manteniment)(2):')}</th><td>${_(u'0.013 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost generació(1+2):')}</th><td>${_(u'0.033 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost final (amb IVPEE 7%)')}</th><td><b>${_(u'0.035 €/kWh')}</b></td></tr>
</table>

<table class="annex1_table">
    <caption><h2>${_(u'Projecte 2:')}</h2></caption>
    <tr><th>${_(u'Tipologia')}</th><td>${_(u'Projecte eòlic')}</td></tr>
    <tr><th>${_(u'Inversión prevista')}</th><td>${_(u'1.750.000 €')}</td></tr>
    <tr><th>${_(u'Producció anual prevista')}</th><td>${_(u'3.593.789 kWh')}</td></tr>
    <tr><th>${_(u'Vida útil considerada:')}</th><td>${_(u'20 anys')}</td></tr>
    <tr><th>${_(u'Període d’amortització:')}</th><td>${_(u'20 anys')}</td></tr>
    <tr><th>${_(u'Valor residual considerat:')}</th><td>${_(u'0 €')}</td></tr>
    <tr><th>${_(u'Cost d’amortització (1):')}</th><td>${_(u'0.024 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost O&M(2):')}</th><td>${_(u'0.016 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost generació(1+2):')}</th><td>${_(u'0.039 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost final (amb IVPEE 7%)')}</th><td><b>${_(u'0.044 €/kWh')}</b></td></tr>
</table>

<table class="annex1_table">
    <caption><h2>${_(u'Projecte 3:')}</h2></caption>
    <tr><th>${_(u'Tipologia:')}</th><td>${_(u'Projecte hidràulic')}</td></tr>
    <tr><th>${_(u'Inversió prevista')}</th><td>${_(u'1.600.000 €')}</td></tr>
    <tr><th>${_(u'Producció anual prevista')}</th><td>${_(u'4.184.615 kWh')}</td></tr>
    <tr><th>${_(u'Vida útil considerada:')}</th><td>${_(u'35 anys')}</td></tr>
    <tr><th>${_(u'Període d’amortització:')}</th><td>${_(u'25 anys')}</td></tr>
    <tr><th>${_(u'Valor residual considerat:')}</th><td>${_(u'215.385 €')}</td></tr>
    <tr><th>${_(u'Cost d’amortització (1):')}</th><td>${_(u'0.013 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost O&M(2):')}</th><td>${_(u'0.015 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost generació(1 + 2):')}</th><td>${_(u'0.027 €/kWh')}</td></tr>
    <tr><th>${_(u'Cost final (con IVPEE 7%+2% cànon hidràulic)')}</th><td><b>${_(u'0.029 €/kWh')}</b></td></tr>
</table>

<table class="annex1_table">
    <caption><h2>${_(u'Determinació Preu Generation kWh:')}</h2></caption>
    <tr><th>${_(u'Projecte')}</th><th>${_(u'Producció anual')}</th><th>${_(u'Inversió')}</th><th>${_(u'Previsió kWh any/A.E. (100€)')}</th><th>${_(u'Cost final')}</th></tr>
    <tr><td>${_(u'1')}</td><td>${_(u'2.818.580 kWh')}</td><td>${_(u'1.800.000 €')}</td><td>${_(u'157')}</td><td>${_(u'0.035 €/kWh')}</td></tr>
    <tr><td>${_(u'2')}</td><td>${_(u'3.593.789 kWh')}</td><td>${_(u'1.750.000 €')}</td><td>${_(u'205')}</td><td>${_(u'0.044 €/kWh')}</td></tr>
    <tr><td>${_(u'3')}</td><td>${_(u'4.184.615 kWh')}</td><td>${_(u'1.600.000 €')}</td><td>${_(u'262')}</td><td>${_(u'0.029 €/kWh')}</td></tr>
</table>
<br/>
<table>
    <tr><th>${_(u'Preu Generation kW')}</th><th>${_(u'Previsió kWh any/Acció Energètica')}</th></tr>
    <tr><td>${_(u'0.036 €/kWh')}</td><td>${_(u'206 kWh')}</td></tr>
</table>

</div>
<p style="page-break-after:always"></p>
<div class="annex2">
<h1>${_(u'ANNEX II')}</h1>
<h1>${_(u'CRITERIS A APLICAR PER A L’ASSIGNACIÓ DE  KWHs ASSOCIATS A CADA ACCIÓ ENERGÈTICA I REPARTIMENT SEGONS PERÍODES TARIFARIS.')}</h1>
<p>${_(u'La producció de les plantes estarà monitoritzada en temps real i cada dia es realitzarà el recompte de la producció que hi ha hagut en cadascun dels diferents períodes tarifaris vigents. En funció d’aquests paràmetres s’establiran les diferents tarifes on se substituirà el preu de l’electricitat al mercat majorista pel preu mitjà de cost de generació de les plantes Generation kWh (Preu Generation kWh), deixant tots els altres conceptes que conformen el preu de de l’electricitat igual.')}</p>
<p>${_(u'D’aquesta manera, el rati kWh per Acció Energètica variarà en funció del període de tarificació. El preu mitjà de cost de generació de les plantes Generation kWh es mantindrà igual en tots els períodes i durant tot l’any.')}</p>

<p><b>${_(u'Per a cada una de les plantes, hem realitzat una inversió determinada:')}</b></p>
<table class="annex2_table">
    <tr><td>${_(u'P1= Projecte 1')}</td><td>${_(u'I1=Inversió P1')}</td></tr>
    <tr><td>${_(u'P2= Projecte 2')}</td><td>${_(u'I2=Inversió P2')}</td></tr>
    <tr><td>${_(u'P3 = Projecte 3')}</td><td>${_(u'I3=Inversió P3')}</td></tr>
    <tr><td>${_(u'(...)')}</td><td></td></tr>
    <tr><td>${_(u'Pn= Projecte n')}</td><td>${_(u'In=Inversió Pn')}</td></tr>
</table>
<p><b>${_(u'Cada una de les plantes té una producció diària (Prd) distribuïda en cada un dels períodes tarifaris diferent:')}</b></p>
<table class="annex2_table">
    <caption><p><b><i>${_(u'En el cas de tarifes sense discriminació horària:')}</i></b></p></caption>
    <tr><td>${_(u'Pd1(0)= Prd.diària P1')}</td></tr>
    <tr><td>${_(u'Pd2(0)= Prd.diària P2')}</td></tr>
    <tr><td>${_(u'Pd3(0)= Prd.diària P3')}</td></tr>
    <tr><td>${_(u'(...)')}</td></tr>
    <tr><td>${_(u'Pdn(0)=Prd. diària Pn')}</td></tr>
</table>

<p>${_(u'Els kWh/Acció Energètica que ens pertoquen per un període de facturació determinat segueix la següent fórmula:')}</p>
<p><b>${_(u'On i= nº dies de facturació')}</b></p>

<p class="math"><b>kWh / A.E.</b>=100*<span class="big_sum">&Sum;</span><sub>de 1 a i</sub> <span class="big_sum">(</span>Pd<sub>i</sub>1(0) + Pd<sub>i</sub>2(0) + Pd<sub>i</sub>3(0) + ... Pd<sub>i</sub>n(0)<span class="big_sum">) / (</span>I1 + I2 + I3 + ... In<span class="big_sum">)</span></p>

<table class="annex2_table">
    <caption><p><b><i>${_(u'En el cas de tarifes amb dos períodes:')}</i></b></p></caption>
    <tr><td>${_(u'Pd1(1)= Prd.diària P1 en p1')}</td><td>${_(u'Pd1(2)= Prd.diària P1 en p2')}</td></tr>
    <tr><td>${_(u'Pd2(1)= Prd.diària P2 en p1')}</td><td>${_(u'Pd2(2)= Prd.diària P2 en p2')}</td></tr>
    <tr><td>${_(u'Pd3(1)= Prd.diària P3 en p1')}</td><td>${_(u'Pd3(2)= Prd.diària P3 en p2')}</td></tr>
    <tr><td>${_(u'(...)')}</td></tr>
    <tr><td>${_(u'Pdn(1)=Prd. diària Pn en p1')}</td><td>${_(u'Pdn(2)=Prd. diària Pn en p2')}</td></tr>
</table>

<p>${_(u'Pel Període P1')}</p>
<p class="math"><b>kWh / A.E.</b>=100*<span class="big_sum">&Sum;</span><sub>de 1 a i</sub> <span class="big_sum">(</span>Pd<sub>i</sub>1(1) + Pd<sub>i</sub>2(1) + Pd<sub>i</sub>3(1) + ... Pd<sub>i</sub>n(1)<span class="big_sum">) / (</span>I1 + I2 + I3 + ... In<span class="big_sum">)</span></p>
<p>${_(u'Pel Període P2')}</p>
<p class="math"><b>kWh / A.E.</b>=100*<span class="big_sum">&Sum;</span><sub>de 1 a i</sub> <span class="big_sum">(</span>Pd<sub>i</sub>1(2) + Pd<sub>i</sub>2(2) + Pd<sub>i</sub>3(2) + ... Pd<sub>i</sub>n(2)<span class="big_sum">) / (</span>I1 + I2 + I3 + ... In<span class="big_sum">)</span></p>

<table class="annex2_table">
    <caption><p><b><i>${_(u'En el cas de tarifes amb tres períodes:')}</i></b></p></caption>
    <tr><td>${_(u'Pd1(1)= Prd.diària P1 en p1')}</td><td>${_(u'Pd1(2)= Prd.diària P1 en p2')}</td><td>${_(u'Pd1(2)= Prd.diària P1 en p3')}</td></tr>
    <tr><td>${_(u'Pd2(1)= Prd.diària P2 en p1')}</td><td>${_(u'Pd2(2)= Prd.diària P2 en p2')}</td><td>${_(u'Pd1(2)= Prd.diària P2 en p3')}</td></tr>
    <tr><td>${_(u'Pd3(1)= Prd.diària P3 en p1')}</td><td>${_(u'Pd3(2)= Prd.diària P3 en p2')}</td><td>${_(u'Pd1(2)= Prd.diària P3 en p3')}</td></tr>
    <tr><td>${_(u'(...)')}</td></tr>
    <tr><td>${_(u'Pdn(1)=Prd. diària Pn en p1')}</td><td>${_(u'Pdn(2)=Prd. diària Pn en p2')}</td><td>${_(u'Pd1(2)= Prd.diària Pn en p3')}</td></tr>
</table>

<p>${_(u'Pel Període P1')}</p>
<p class="math"><b>kWh / A.E.</b>=100*<span class="big_sum">&Sum;</span><sub>de 1 a i</sub> <span class="big_sum">(</span>Pd<sub>i</sub>1(1) + Pd<sub>i</sub>2(1) + Pd<sub>i</sub>3(1) + ... Pd<sub>i</sub>n(1)<span class="big_sum">) / (</span>I1 + I2 + I3 + ... In<span class="big_sum">)</span></p>
<p>${_(u'Pel Període P2')}</p>
<p class="math"><b>kWh / A.E.</b>=100*<span class="big_sum">&Sum;</span><sub>de 1 a i</sub> <span class="big_sum">(</span>Pd<sub>i</sub>1(2) + Pd<sub>i</sub>2(2) + Pd<sub>i</sub>3(2) + ... Pd<sub>i</sub>n(2)<span class="big_sum">) / (</span>I1 + I2 + I3 + ... In<span class="big_sum">)</span></p>
<p>${_(u'Pel Període P3')}</p>
<p class="math"><b>kWh / A.E.</b>=100*<span class="big_sum">&Sum;</span><sub>de 1 a i</sub> <span class="big_sum">(</span>Pd<sub>i</sub>1(3) + Pd<sub>i</sub>2(3) + Pd<sub>i</sub>3(3) + ... Pd<sub>i</sub>n(3)<span class="big_sum">) / (</span>I1 + I2 + I3 + ... In<span class="big_sum">)</span></p>
</div>

<b>${_(u'A nivell d’Exemple:')}</b>
<table class="annex1_table">
    <caption>${_(u'-Considerant una tarifa 3.0A amb tres períodes.')}</caption>
    <tr>
        <th><b>${_(u'Projectes')}</b></th>
        <th><b>${_(u'Inversió')}</b></th>
        <th><b>${_(u'Producció total dia (i)')}</b></th>
        <th><b>${_(u'Producció en p1')}</b></th>
        <th><b>${_(u'Producció en p2')}</b></th>
        <th><b>${_(u'Producció en p3')}</b></th>
    </tr>
    <tr>
        <td>${_(u'P1')}</td>
        <td>${_(u'1.800.000')}</td>
        <td>${_(u'7.722')}</td>
        <td>${_(u'2.085')}</td>
        <td>${_(u'5.483')}</td>
        <td>${_(u'232')}</td>
    </tr>
    <tr>
        <td>${_(u'P2')}</td>
        <td>${_(u'1.750.000')}</td>
        <td>${_(u'9.846')}</td>
        <td>${_(u'1.477')}</td>
        <td>${_(u'4.726')}</td>
        <td>${_(u'3.643')}</td>
    </tr>
    <tr>
        <td>${_(u'P3')}</td>
        <td>${_(u'1.600.000')}</td>
        <td>${_(u'11.465')}</td>
        <td>${_(u'1.911')}</td>
        <td>${_(u'5.732')}</td>
        <td>${_(u'3.822')}</td>
    </tr>
    <tr>
        <td>${_(u'Total')}</td>
        <td>${_(u'5.150.000')}</td>
        <td>${_(u'29.033')}</td>
        <td>${_(u'5.473')}</td>
        <td>${_(u'15.941')}</td>
        <td>${_(u'7.696')}</td>
    </tr>
    <tr>
        <td><b>${_(u'kWh/dia (i)*. Acció Energètica')}</b></td>
        <td></td>
        <td></td>
        <td><b>${_(u'0.106 kWh')}</b></td>
        <td><b>${_(u'0.310 kWh')}</b></td>
        <td><b>${_(u'0.149 kWh')}</b></td>
    </tr>
</table>
<i>${_(u'* les dades són per un dia mitjà anual.')}</i>
%endfor
</body>
</html>
