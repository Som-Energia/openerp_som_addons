<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<head>
    <style type="text/css">
    ${css}
    body {
        margin-top: 50px;
        font-family: helvetica;
        font-size: 14px;
    }
    p {
        padding: 12px;
    }
    td {
        padding: 5px;
    }
    .title {
      text-transform: uppercase;
      text-align: right;
      font-size: 22px;
    }

    .subtitle {
      padding-top: 50px;
      text-align: right;
      font-size: 20px;
    }
    .label {
      width: 150px;
    }
    </style>
</head>
<body>
    %for inv in objects :
    <% setLang(inv.partner_id.lang) %>
    <img style="float: left; margin-top: -60px;" src="${addons_path}/som_inversions/report/logo.jpg" width="150" height="150"/>
    <h1 class="title">
      ${_("Informació fiscal")} ${inv.date_invoice.split('-')[0]}
    </h1>
    <h2 class="subtitle">
      ${_("Comunicat de rendiments per a la declaració de renda")} ${inv.date_invoice.split('-')[0]}
    </h2>
    <hr />
    <table>
      <tr>
        <td class="label">${_("Data")}:</td>
        <td>${formatLang(time.strftime('%Y-%m-%d'), date=True)}</td>
      </tr>
      <tr>
        <td class="label">${_("Exercici")}:</td>
        <td class="text">${inv.date_invoice.split('-')[0]}</td>
      </tr>
      <tr>
        <td class="label">${_("Nom de l'entitat")}:</td>
        <td class="text">${inv.company_id.partner_id.name}</td>
      </tr>
      <tr>
        <td class="label">${_("NIF entitat")}:</td>
        <td class="text">${inv.company_id.partner_id.vat[2:]}</td>
      </tr>
      <tr>
        <td class="label">${_("Tipus inversió")}:</td>
        % if inv.journal_id.code == 'APO':
            <td class="text">${_("aportacions voluntàries al capital social")}</td>
        % elif inv.journal_id.code == 'TIT':
            <td class="text">${_("títols participatius")}</td>
        % else:
            <td></td>
        % endif

      </tr>
    </table>
    <hr />
    <table>
      <tr>
        <td class="label">${_("Titular")}:</td>
        <td class="text">${inv.partner_id.name}</td>
      </tr>
      <tr>
        <td class="label">${_("NIF titular")}:</td>
        <td class="text">${inv.partner_id.vat[2:]}</td>
      </tr>
    </table>
    <hr />
    <table>
      <tr>
        <td class="label">${_("Rendiments bruts")}:</td>
        <td class="text">${formatLang(inv.amount_untaxed, monetary=True)}</td>
      </tr>
      <tr>
        <td class="label">${_("Retenció a compte")}:</td>
        <td class="text">${formatLang(abs(inv.amount_tax), monetary=True)}</td>
      </tr>
      <tr>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td colspan="2">${_("Informació addicional:")}</td>
      </tr>
      <tr>
        <td class="label">${_("Saldo a")} ${formatLang(inv.date_invoice, date=True)}:</td>
        % if inv.journal_id.code == 'APO':
            <td class="text">${formatLang(abs(inv.partner_id.property_account_aportacions.balance), monetary=True)}</td>
        % elif inv.journal_id.code == 'TIT':
            <td class="text">${formatLang(abs(inv.partner_id.property_account_titols.balance), monetary=True)}</td>
        % endif
      </tr>
    </table>
    <img src="${addons_path}/som_inversions/report/peu.jpg" width="650px" style="margin-top: 200px;"/>
    <p style="page-break-after:always"></p>
    %endfor
</body>
</html>
