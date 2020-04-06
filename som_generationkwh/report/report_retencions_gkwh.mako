<%
    report = objects[0]
    data = report.generationkwh_amortization_data()
%>

<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<head>
    <style type="text/css">
    ${css}
    body {
        margin-top: 100px;
        font-size: 14px;
        margin-left: 70px;
        margin-right: 70px;
    }
    p {
        padding: 12px;
    }
    td {
        padding: 5px;
    }
    .title {
        margin-top:90px;
        text-transform: uppercase;
        text-align: right;
        font-size: 22px;
    }
    .logo_footer{
        position: fixed;
        display: block;
        margin-top: 110px;
        font-size: 10px;
    }
    .subtitle {
      padding-top: 50px;
      text-align: left;
      font-size: 16px;
    }
    .label {
      width: 150px;
    }
    </style>
</head>
<body>

    %for investment in objects :
    <%
    setLang(data.language)

    %>
     <img  style="float: left; position: fixed; z-index:-1; margin-top: -10px;" src="${addons_path}/som_inversions/report/logo.jpg" width="150" height="150"/>
    <div class="logo_footer">
     <span style="font-weight: bold;">${data.partner_name}</span><br/>
        ${_(u"CIF:")} ${data.partner_vat.replace('ES','')} <br />
        ${_(u"Domicili:")} ${data.address_street} ${data.address_zip} - ${data.address_city}<br/>
        ${_(u"Adreça electrònica:")} ${data.address_email}<br/>
    </div>
    <br/>
    <h1 class="title">
      ${_("Informació fiscal")}
    </h1>
    <h2 class="subtitle">
      ${_("Comunicat de rendiments per a la declaració de renda")} ${data.year}
    </h2>
    <hr />
    <table>
      <tr>
        <td class="label">${_("Data")}:</td>
        <td>${formatLang(time.strftime('%Y-%m-%d'), date=True)}</td>
      </tr>
      <tr>
        <td class="label">${_("Exercici")}:</td>
        <td class="text">${data.year}</td>
      </tr>
      <tr>
        <td class="label">${_("Tipus d'aportació")}:</td>
            <td class="text">${_("Generation kWh")}</td>
      </tr>
    </table>
    <hr />
    <table>
      <tr>
        <td class="label">${_("Titular")}:</td>
        <td class="text">${data.member_name}</td>
      </tr>
      <tr>
        <td class="label">${_("NIF titular")}:</td>
        <td class="text">${data.member_vat}</td>
      </tr>
    </table>
    <hr/>
    <table>
      <tr>
        <td class="label">${_("Estalvi")}:</td>
        <td class="text">${formatLang(data.estalvi, monetary=True)}</td>
      </tr>
      <tr>
        <td class="label">${_("19% Retenció sobre l'estalvi")}:</td>
        <td class="text">${formatLang(data.retencio, monetary=True)}</td>
      </tr>
    </table>
    %endfor
</body>
</html>
