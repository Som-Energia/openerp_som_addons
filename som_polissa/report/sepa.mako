## -*- encoding: utf-8 -*-
<%
report = objects[0]
data = report.sepa_particulars_data()
%>

<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
    <link rel="stylesheet" href="${addons_path}/som_polissa/report/sepa.css"/>
</head>
<body>
<div class="extern margin50">
    <div>
        <img id="logo" width='105px' src="https://www.somenergia.coop/wp-content/uploads/2014/11/logo-somenergia.png">
        <div class="centered title">
            % if data['is_business']:
            <h1>Orden de domiciliación de adeudo directo SEPA B2B</h1>
            <h2>SEPA Business-to-Business Direct Debit Mandate</h2>
            % else:
            <h1>Orden de domiciliación de adeudo directo SEPA</h1>
            <h2>SEPA Direct Debit Mandate</h2>
            % endif
        </div>
    </div>
    <div>
        <div class="centered blau">A cumplimentar por el acreedor /
            <span class="english">To be completed by the creditor</span>
        </div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Referencia de la orden de domiciliación / <span class="english">Mandate reference</span></p>
            <p class="entrada">${data['order_reference']}</p></div>
            <div class="parella"><p class="label">Identificador del acreedor / <span class="english">Creditor identifier</span></p>
            <p class="entrada">${data['creditor_code']}</p></div>
            <div class="parella"><p class="label">Nombre del acreedor / <span class="english">Creditor´s name</span></p>
            <p class="entrada">${data['creditor_name']}</p></div>
            <div class="parella"><p class="label">Dirección /<span class="english">Address</span></p>
            <p class="entrada">${data['creditor_address']}</p></div>
            <div class="parella"><p class="label">Provincia / <span class="english">Province </span></p>
            <p class="entrada">${data['creditor_province']}</p></div>
            <div class="parella"><p class="label">País / <span class="english">Country</span></p>
            <p class="entrada">${data['creditor_country']}</p></div>
        </div>
    </div>
    <div>
        % if data['is_business']:
        <p class="margin20 spanish">
        Mediante la firma de esta orden de domiciliación, el deudor autoriza (A) al acreedor a enviar instrucciones a la entidad del deudor para adeudar su cuenta y (B) a la entidad para efectuar los adeudos en su cuenta siguiendo las instrucciones del acreedor. Esta orden de domiciliación está prevista para operaciones exclusivamente entre empresas y/o autónomos. El deudor no tiene derecho a que su entidad le reembolse una vez que se haya realizado el cargo en cuenta, pero puede solicitar a su entidad que no efectúe el adeudo en la cuenta hasta la fecha debida. Podrá obtener información detallada del procedimiento en su entidad financiera.
        </p>
        <p class="margin20 english">
        By signing this mandate form, you authorize (A) the Creditor to send instructions to your bank to debit your account and (B) your bank to debit your account in accordance with the instructions from the Creditor. This mandate is only intended for business-to-business transactions. You are not entitled to a refund from your bank after your account has been debited, but you are entitled to request your bank not to debit your account up until the day on which the payment is due. Please contact your bank for detailed procedures in such a case.
        </p>
        % else:
        <p class="margin20">
        Mediante la firma de esta orden de domiciliación, el deudor autoriza (A) al acreedor a enviar instrucciones a la entidad del deudor para adeudar su cuenta y (B) a la entidad para efectuar los adeudos en su cuenta siguiendo las instrucciones del acreedor. Como parte de sus derechos, el deudor está legitimado al reembolso por su entidad en los términos y condiciones del contrato suscrito con la misma. La solicitud de reembolso deberá efectuarse dentro de las ocho semanas que siguen a la fecha de adeudo en cuenta. Puede obtener información adicional sobre sus derechos en su entidad financiera.
        </p>
        <p class="margin20 english">
        By signing this mandate form, you authorise (A) the Creditor to send instructions to your bank to debit your account and (B) your bank to debit your account in accordance with the instructions from the Creditor. As part of your rights, you are entitled to a refund from your bank under the terms and conditions of your agreement with your bank. A refund must be claimed within eigth weeks starting from the date on which your account was debited. Your rights are explained in a statement that you can obtain from your bank.
        </p>
        % endif
    </div>
    <div>
        <div class="centered blau">A cumplimentar por el deudor /
            <span class="english">To be completed by the debtor</span>
        </div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Nombre del deudor/es (titular/es de la cuenta de cargo) / <span class="english">Debtor’s name</span></p>
            <p class="entrada">${data['debtor_name']}</p></div>
            <div class="parella"><p class="label">Dirección del deudor / <span class="english">Address of the debtor</span></p>
            <p class="entrada">${data['debtor_address']}</p></div>
            <div class="parella"><p class="label">Provincia / <span class="english">Province</span></p>
            <p class="entrada">${data['debtor_province']}</p></div>
            <div class="parella"><p class="label">País del deudor / <span class="english">Country of the debtor</span></p>
            <p class="entrada">${data['debtor_country']}</p></div>
            <div class="parella"><p class="label">Swift BIC / <span class="english">Swift BIC (puede contener 8 u 11 posiciones) / Swift BIC (up to 8 or 11 characters)</span></p>
            <p class="entrada entrada-alta">${data['swift']}</p></div>
            <div class="parella"><p class="label">Número de cuenta - IBAN / <span class="english">Account number - IBAN</span></p>
            <p class="entrada entrada-alta">${data['debtor_iban_print']}</p></div>
            <p class="english">En España el IBAN consta de 24 posiciones comenzando siempre por ES / Spanish IBAN of 24 positions always starting ES</p>
            <div>
                <div class="parella"><p class="label">Tipo de pago / <span class="english">Type of payment</span>:</p>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['recurring']}>Pago recurrente / <span class="english">Recurrent payment</span>
                </label>
                <label  class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['single_payment']}>Pago único / <span class="english">One-off payment</span>
                </label>
            </div>
            <div class="parella"><p class="label">Fecha - Localidad / <span class="english">Date - location in which you are signing</span>:</p>
            <p class="entrada">${data['sign_date']} - ${data['creditor_city']}</p></div>
            <div class="parella"><p class="label">Firma del deudor / <span class="english">Signature of the debtor</span>:</p>
            <p class="entrada entrada-molt-alta"></p></div>
        </div>
    </div>
    <div class="last">
        % if data['is_business']:
        <p class="spanish centered">
            TODOS LOS CAMPOS HAN DE SER CUMPLIMENTADOS OBLIGATORIAMENTE.
            UNA VEZ FIRMADA ESTA ORDEN DE DOMICILIACIÓN DEBE SER ENVIADA AL ACREEDOR PARA SU CUSTODIA.
            LA ENTIDAD DE DEUDOR REQUIERE AUTORIZACIÓN DE ÉSTE PREVIA AL CARGO EN CUENTA DE LOS ADEUDOS DIRECTOS B2B.
            EL DEUDOR PODRÁ GESTIONAR DICHA AUTORIZACIÓN CON LOS MEDIOS QUE SU ENTIDAD PONGA A SU DISPOSICIÓN.
            <br>
        <p class="english centered">ALL GAPS ARE MANDATORY. ONCE THIS MANDATE HAS BEEN SIGNED MUST BE SENT TO CREDITOR FOR STORAGE. NEVERTHELESS, THE BANK OF DEBTOR REQUIRES DEBTOR’S AUTHORIZATION
            BEFORE DEBITING B2B DIRECT DEBITS IN THE ACCOUNT. THE DEBTOR WILL BE ABLE TO MANAGE THE MENTIONED AUTHORIZATION THROUGH THE MEANS PROVIDED BY HIS BANK.</p>
        </p>
        % else:
        <p class="spanish centered">
            TODOS LOS CAMPOS HAN DE SER CUMPLIMENTADOS OBLIGATORIAMENTE.

            UNA VEZ FIRMADA ESTA ORDEN DE DOMICILIACIÓN DEBE SER ENVIADA AL ACREEDOR PARA SU CUSTODIA.
            <br>
        </p>
        <p class="english centered">ALL GAPS ARE MANDATORY. ONCE THIS MANDATE HAS BEEN SIGNED MUST BE SENT TO CREDITOR FOR STORAGE.</p>
        % endif
    </div>
</div>
</body>
</html>
