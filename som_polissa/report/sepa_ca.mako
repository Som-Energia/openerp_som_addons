## -*- encoding: utf-8 -*-
<%def name="sepa_ca(data, page_break)">
<div class="extern margin50${' mandate-page' if page_break else ''}">
    <div>
        <img id="logo" width="105px" src="data:image/jpeg;base64,${data['company_logo']}">
        <div class="centered title">
            %if data['is_business']:
                <h1>Ordre de domiciliació de dèbit directe SEPA B2B</h1>
                <h2>SEPA Business-to-Business Direct Debit Mandate</h2>
            %else:
                <h1>Ordre de domiciliació de dèbit directe SEPA</h1>
                <h2>SEPA Direct Debit Mandate</h2>
            %endif
        </div>
    </div>
    <div>
        <div class="centered blau">A emplenar pel creditor /
            <span class="english">To be completed by the creditor</span>
        </div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Referència de l'ordre de domiciliació / <span class="english">Mandate reference</span></p>
            <p class="entrada">${data['order_reference']}</p></div>
            <div class="parella"><p class="label">Identificador del creditor / <span class="english">Creditor identifier</span></p>
            <p class="entrada">${data['creditor_code']}</p></div>
            <div class="parella"><p class="label">Nom del creditor / <span class="english">Creditor´s name</span></p>
            <p class="entrada">${data['creditor_name']}</p></div>
            <div class="parella"><p class="label">Adreça / <span class="english">Address</span></p>
            <p class="entrada">${data['creditor_address']}</p></div>
            <div class="parella"><p class="label">Província / <span class="english">Province </span></p>
            <p class="entrada">${data['creditor_province']}</p></div>
            <div class="parella"><p class="label">País / <span class="english">Country</span></p>
            <p class="entrada">${data['creditor_country']}</p></div>
        </div>
    </div>
    <div>
        %if data['is_business']:
            <p class="margin20 spanish">
            Mitjançant la signatura d'aquesta ordre de domiciliació, el deutor autoritza (A) el creditor a enviar instruccions a l'entitat del deutor perquè carregui imports al seu compte i (B) l'entitat a efectuar els càrrecs al seu compte seguint les instruccions del creditor. Aquesta ordre de domiciliació està prevista exclusivament per a operacions entre empreses i/o autònoms. El deutor no té dret que la seva entitat li reemborsi l'import un cop s'hagi efectuat el càrrec en compte, però pot sol·licitar a la seva entitat que no efectuï el càrrec al compte fins a la data de venciment. Pot obtenir informació detallada sobre el procediment a la seva entitat financera.
            </p>
            <p class="margin20 english">
            By signing this mandate form, you authorize (A) the Creditor to send instructions to your bank to debit your account and (B) your bank to debit your account in accordance with the instructions from the Creditor. This mandate is only intended for business-to-business transactions. You are not entitled to a refund from your bank after your account has been debited, but you are entitled to request your bank not to debit your account up until the day on which the payment is due. Please contact your bank for detailed procedures in such a case.
            </p>
        %else:
            <p class="margin20">
            Mitjançant la signatura d'aquesta ordre de domiciliació, el deutor autoritza (A) el creditor a enviar instruccions a l'entitat del deutor perquè carregui imports al seu compte i (B) l'entitat a efectuar els càrrecs al seu compte seguint les instruccions del creditor. Com a part dels seus drets, el deutor té dret al reemborsament per part de la seva entitat en els termes i les condicions del contracte subscrit amb aquesta. La sol·licitud de reemborsament s'haurà d'efectuar dins de les vuit setmanes següents a la data del càrrec en compte. Pot obtenir informació addicional sobre els seus drets a la seva entitat financera.
            </p>
            <p class="margin20 english">
            By signing this mandate form, you authorise (A) the Creditor to send instructions to your bank to debit your account and (B) your bank to debit your account in accordance with the instructions from the Creditor. As part of your rights, you are entitled to a refund from your bank under the terms and conditions of your agreement with your bank. A refund must be claimed within eigth weeks starting from the date on which your account was debited. Your rights are explained in a statement that you can obtain from your bank.
            </p>
        %endif
    </div>
    <div>
        <div class="centered blau">A emplenar pel deutor /
            <span class="english">To be completed by the debtor</span>
        </div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Nom del deutor/s / <span class="english">Debtor’s name</span></p>
            <p class="entrada">${data['debtor_name']}</p></div>
            <div class="parella"><p class="label">Adreça del deutor / <span class="english">Address of the debtor</span></p>
            <p class="entrada">${data['debtor_address']}</p></div>
            <div class="parella"><p class="label">Província / <span class="english">Province</span></p>
            <p class="entrada">${data['debtor_province']}</p></div>
            <div class="parella"><p class="label">País del deutor / <span class="english">Country of the debtor</span></p>
            <p class="entrada">${data['debtor_country']}</p></div>
            <div class="parella"><p class="label">Swift BIC / <span class="english">Swift BIC (pot contenir 8 o 11 posicions) / Swift BIC (up to 8 or 11 characters)</span></p>
            <p class="entrada entrada-alta">${data['swift']}</p></div>
            <div class="parella"><p class="label">Número de compte - IBAN / <span class="english">Account number - IBAN</span></p>
            <p class="entrada entrada-alta">${data['debtor_iban_print']}</p></div>
            <p class="english">A Espanya l'IBAN consta de 24 posicions i comença sempre per ES / Spanish IBAN of 24 positions always starting ES</p>
            <div class="parella">
                <p class="label">Tipus de pagament / <span class="english">Type of payment</span>:</p>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['recurring']}>Pagament recurrent / <span class="english">Recurrent payment</span>
                </label>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['single_payment']}>Pagament únic / <span class="english">One-off payment</span>
                </label>
            </div>
            <div class="parella"><p class="label">Data - Localitat / <span class="english">Date - location in which you are signing</span>:</p>
            <p class="entrada">${data['sign_date']} - ${data['creditor_city']}</p></div>
            <div class="parella"><p class="label">Signatura del deutor / <span class="english">Signature of the debtor</span>:</p>
            <p class="entrada entrada-molt-alta"></p></div>
        </div>
    </div>
    <div class="last">
        %if data['is_business']:
            <p class="spanish centered">
                TOTS ELS CAMPS S'HAN D'EMPLENAR OBLIGATÒRIAMENT.
                UN COP SIGNADA, AQUESTA ORDRE DE DOMICILIACIÓ S'HA D'ENVIAR AL CREDITOR PERQUÈ LA CUSTODIÏ.
                L'ENTITAT DEL DEUTOR REQUEREIX L'AUTORITZACIÓ PRÈVIA D'AQUEST ABANS DE CARREGAR ELS DÈBITS DIRECTES B2B AL COMPTE.
                EL DEUTOR PODRÀ GESTIONAR AQUESTA AUTORITZACIÓ MITJANÇANT ELS CANALS QUE LA SEVA ENTITAT POSI A LA SEVA DISPOSICIÓ.
                <br>
            </p>
            <p class="english centered">ALL GAPS ARE MANDATORY. ONCE THIS MANDATE HAS BEEN SIGNED MUST BE SENT TO CREDITOR FOR STORAGE. NEVERTHELESS, THE BANK OF DEBTOR REQUIRES DEBTOR’S AUTHORIZATION
                BEFORE DEBITING B2B DIRECT DEBITS IN THE ACCOUNT. THE DEBTOR WILL BE ABLE TO MANAGE THE MENTIONED AUTHORIZATION THROUGH THE MEANS PROVIDED BY HIS BANK.</p>
        %else:
            <p class="spanish centered">
                TOTS ELS CAMPS S'HAN D'EMPLENAR OBLIGATÒRIAMENT.
                UN COP SIGNADA, AQUESTA ORDRE DE DOMICILIACIÓ S'HA D'ENVIAR AL CREDITOR PERQUÈ LA CUSTODIÏ.
                <br>
            </p>
            <p class="english centered">ALL GAPS ARE MANDATORY. ONCE THIS MANDATE HAS BEEN SIGNED MUST BE SENT TO CREDITOR FOR STORAGE.</p>
        %endif
    </div>
</div>
</%def>
