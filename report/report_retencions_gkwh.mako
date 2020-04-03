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
    }
    .subtitle {
      padding-top: 50px;
      text-align: left;
      font-size: 20px;
    }
    .label {
      width: 150px;
    }
    </style>
</head>
<body>
<%
    from datetime import timedelta, datetime, date
    Investment = objects[0].pool.get('generationkwh.investment')
    ResPartner = objects[0].pool.get('res.partner')
    ResPartnerAdress = objects[0].pool.get('res.partner.address')
    partner_id = 1#ResPartner.search(cursor, uid, [('vat','=','ESF55091367')])
    partner = ResPartner.read(cursor, uid, partner_id, ['name','vat','address'])
    address = ResPartnerAdress.read(cursor, uid, partner['address'][0], ['street','zip','city','email'])
    year = (datetime.now() - timedelta(days=365)).year
%>
    %for investment in objects :
    <%
    setLang(investment.member_id.partner_id.lang)
    member_id = investment.member_id.id
    investment_id = investment.id
    partner_id = investment.member_id.partner_id.id
    data_inici = date(year, 1, 1).isoformat()
    data_fi = date(year, 12, 31).isoformat()
    estalvi = Investment.get_total_saving_partner(cursor, uid, partner_id, data_inici, data_fi)
    retencio = Investment.get_irpf_amount(cursor, uid, investment_id , member_id, year)
    %>
     <img  style="float: left; position: fixed; z-index:-1; margin-top: -10px;" src="${addons_path}/som_inversions/report/logo.jpg" width="150" height="150"/>
    <div class="logo_footer">
     <span style="font-weight: bold;">${partner['name']}</span><br/>
        ${_(u"CIF:")} ${partner['vat'].replace('ES','')} <br />
        ${_(u"Domicili:")} ${address['street']} ${address['zip']} - ${address['city']}<br/>
        ${_(u"Adreça electrònica:")} ${address['email']}<br/>
    </div>
    <br/>
    <h1 class="title">
      ${_("Informació fiscal")}
    </h1>
    <h2 class="subtitle">
      ${_("Comunicat de rendiments per a la declaració de renda")} ${year}
    </h2>
    <hr />
    <table>
      <tr>
        <td class="label">${_("Data")}:</td>
        <td>${formatLang(time.strftime('%Y-%m-%d'), date=True)}</td>
      </tr>
      <tr>
        <td class="label">${_("Exercici")}:</td>
        <td class="text">${year}</td>
      </tr>
      <tr>
        <td class="label">${_("Tipus d'aportació")}:</td>
            <td class="text">${_("Aportacions en Generation kWh")}</td>
      </tr>
    </table>
    <hr />
    <table>
      <tr>
        <td class="label">${_("Titular")}:</td>
        <td class="text">${investment.member_id.partner_id.name}</td>
      </tr>
      <tr>
        <td class="label">${_("NIF titular")}:</td>
        <td class="text">${investment.member_id.partner_id.vat[2:]}</td>
      </tr>
    </table>
    <hr/>
    <table>
      <tr>
        <td class="label">${_("Estalvi")}:</td>
        <td class="text">${formatLang(estalvi, monetary=True)}</td>
      </tr>
      <tr>
        <td class="label">${_("19% Retenció sobre l'estalvi")}:</td>
        <td class="text">${formatLang(retencio, monetary=True)}</td>
      </tr>
    </table>
    %endfor
</body>
</html>
