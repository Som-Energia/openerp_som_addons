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
