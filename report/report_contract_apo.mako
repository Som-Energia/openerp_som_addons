<%
    report = objects[0]
    data = report.investmentCreationAPO_notificationData()
%>
<html>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

<head>
    <title>${_(u"Liquidació préstec Generation kWh")}</title>
    <style type="text/css">
    ${css}
    img {
        width: 120px;
        height: 120px;
        margin-left: 10px;
    }
    .logos {
        float: left;
    }
    table a:link {
        color: #666;
        font-weight: bold;
        text-decoration:none;
    }
    table {
        font-family:Arial, Helvetica, sans-serif;
        color:#666;
        font-size:12px;
        text-shadow: 1px 1px 0px #fff;
        background:#e0e0e0;
        margin-left:auto;
        margin-right:auto;
        width: 60%;
        border:#ccc 1px solid;

        -moz-border-radius:3px;
        -webkit-border-radius:3px;
        border-radius:3px;

        -moz-box-shadow: 0 1px 2px #d1d1d1;
        -webkit-box-shadow: 0 1px 2px #d1d1d1;
        box-shadow: 0 1px 2px #d1d1d1;
    }
    table th {
        padding:10px 25px;
        border-top:1px solid #fafafa;
        border-bottom:1px solid #e0e0e0;

        background: #ededed;
        background: -webkit-gradient(linear, left top, left bottom, from(#ededed), to(#ebebeb));
        background: -moz-linear-gradient(top,  #ededed,  #ebebeb);
    }
    table th:first-child {
        text-align: center;
        padding-left:20px;
    }
    table tr:first-child th:first-child {
        -moz-border-radius-topleft:3px;
        -webkit-border-top-left-radius:3px;
        border-top-left-radius:3px;
    }
    table tr:first-child th:last-child {
        -moz-border-radius-topright:3px;
        -webkit-border-top-right-radius:3px;
        border-top-right-radius:3px;
    }
    table tr:last-child td:first-child {
        -moz-border-radius-bottomleft:3px;
        -webkit-border-bottom-left-radius:3px;
        border-bottom-left-radius:3px;
    }
    table tr:last-child td:last-child {
        -moz-border-radius-bottomright:3px;
        -webkit-border-bottom-right-radius:3px;
        border-bottom-right-radius:3px;
    }
    table tr {
        text-align: left;
        padding-left:20px;
    }
    table td:first-child {
        padding-left:20px;
        border-left: 0;
    }
    table td {
        padding:5px 18px;
        border-top: 1px solid #ffffff;
        border-bottom:1px solid #e0e0e0;
        border-left: 1px solid #e0e0e0;

        background: #fafafa;
        background: -webkit-gradient(linear, left top, left bottom, from(#fbfbfb), to(#fafafa));
        background: -moz-linear-gradient(top,  #fbfbfb,  #fafafa);
    }
    table tr:last-child td {
        border-bottom:0;
    }
    #account{
        text-align: center;
    }
    #cabecera{
        float: right;
        padding-top: 20px;
        text-align: right;
    }
    #warning24{
        font-size: 75%;
        vertical-align: text-bottom;
    }

    </style>
</head>
<body>
<% 
for account.invoice in objects:
 setLang(account.invoice.lang_partner)
%>
    <div class="logos">
        <img src="${addons_path}/som_generationkwh/report/Logo-SomEnergia-blanco-quadrado-250x250px.jpg" />
        <p id="cabecera"><b>Liquidació GenerationkWh</b><br>Emisió: ${data.receiptDate} </ p>
    </ div>
    <div>
    <table>
        <tr>
            <th colspan="2"><b>${_(u"Dades Préstec Generation kWh: ")} ${data.inversionName}</b></th>
        </tr>
        <tr>
            <td colspan="2"> ${_(u"Titular: ")}${data.ownerName}</td>

        </tr>
        <tr>
            <td> ${_(u"NIF: ")} ${data.ownerNif} </td>
            <td> ${_(u"Import Inicial: ")} ${data.inversionInitialAmount} € </td>
        </tr>
        <tr>
            <td> ${_(u"Data formalització: ")}${data.inversionPurchaseDate}</td>
            <td> ${_(u"Data venciment: ")}${data.inversionExpirationDate}</td>
        </tr>
    </table>
    </br>
    </br>
    <table>
        <tr>
            <th colspan="2"><b> ${_(u"Compte on es realizarà l'ingrés")}</b></th>
        </tr>
        <tr>
            <td id="account"> ${data.inversionBankAccount} </td>
        </tr>
    </table>
    </div>
</body>
</html>
