<%page args="d" />
<%
    setLang(d.lang)
%>
<div class="extern margin50">
    <div>
        <img id="logo" width='105px' src="https://www.somenergia.coop/wp-content/uploads/2014/11/logo-somenergia.png">
        <div class="centered title">
            % if d['is_business']:
            <h1>${_(u'Ordre SEPA de domiciliació de dèbit directe d’empresa a empresa')}</h1>
            <h2>SEPA Business-to-Business Direct Debit Mandate</h2>
            % else:
            <h1>${_(u'Ordre de domiciliació de dèbit directe SEPA')}</h1>
            <h2>SEPA Direct Debit Mandate</h2>
            % endif
        </div>
    </div>
    <div>
        <div class="centered blau">${_(u'A completar pel creditor')} /
            <span class="english">To be completed by the creditor</span>
        </div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">${_(u'Referència de l’ordre de domiciliació')} /<span class="english">Mandate reference</span></p>
            <p class="entrada">${d['order_reference']}</p></div>
            <div class="parella"><p class="label">${_(u'Identificador del creditor')} /<span class="english">Creditor identifier</span></p>
            <p class="entrada">${d['creditor_code']}</p></div>
            <div class="parella"><p class="label">${_(u'Nom del creditor')} /<span class="english">Creditor´s name</span></p>
            <p class="entrada">${d['creditor_name']}</p></div>
            <div class="parella"><p class="label">${_(u'Adreça')} /<span class="english">Address</span></p>
            <p class="entrada">${d['creditor_address']}</p></div>
            <div class="parella"><p class="label">${_(u'Codi postal - Població - Província')} /<span class="english">Postal code - City - Town  </span></p>
            <p class="entrada">${d['creditor_zip']} - ${d['creditor_city']} - ${d['creditor_province']}</p></div>
            <div class="parella"><p class="label">${_(u'País')} /<span class="english">Country</span></p>
            <p class="entrada">${d['creditor_country']}</p></div>
        </div>
    </div>
    <div>
        % if d['is_business']:
        <p class="margin20 spanish">
        ${_(u'Mitjançant la signatura d’aquest formulari d’ordre de domiciliació el autoritzeu a (A) SOM ENERGIA, SCCL a enviar ordres a la vostre entitat financera per debitar càrrecs al vostre compte i (B) a la seva entitat financera per debitar els imports corresponents al vostre compte d’acord amb les instruccions de SOM ENERGIA, SCCL. Aquesta ordre de domiciliació està prevista exclusivament per a operacions de empresa a empresa. Vostè no té dret a que la seva entitat li reemborsi una vegada que s’hagi debitat al seu compte, però té dret a sol·licitar a la seva entitat financera que no debiti el seu compte fins a la data de venciment per al cobrament del dèbit. Poseu-vos en contacte amb el vostre banc per obtenir els procediments detallats en aquest cas.')}
        </p>
        <p class="margin20 english">
        By signing this mandate form, you authorize (A) the Creditor to send instructions to your bank to debit your account and (B) your bank to debit your account in accordance with the instructions from the Creditor. This mandate is only intended for business-to-business transactions. You are not entitled to a refund from your bank after your account has been debited, but you are entitled to request your bank not to debit your account up until the day on which the payment is due. Please contact your bank for detailed procedures in such a case.
        </p>
        % else:
        <p class="margin20">
        ${_(u'Mitjançant la signatura d’aquesta ordre de domiciliació, el deutor autoritza (A) el creditor a enviar instruccions a l’entitat del deutor per deure el compte i (B) l’entitat per efectuar els deutes al compte seguint les instruccions del creditor. Com a part dels seus drets, el deutor està legitimat al reemborsament per la seva entitat en els termes i les condicions del contracte subscrit amb aquesta. La sol·licitud de reemborsament s’ha d’efectuar dins de les vuit setmanes que segueixen la data de càrrec en compte. Podeu obtenir informació addicional sobre els vostres drets a la vostra entitat financera.')}
        </p>
        <p class="margin20 english">
        By signing this mandate form, you authorise (A) the Creditor to send instructions to your bank to debit your account and (B) your bank to debit your account in accordance with the instructions from the Creditor. As part of your rights, you are entitled to a refund from your bank under the terms and conditions of your agreement with your bank. A refund must be claimed within eigth weeks starting from the date on which your account was debited. Your rights are explained in a statement that you can obtain from your bank.
        </p>
        % endif
    </div>
    <div>
        <div class="centered blau">${_(u'A completar pel deutor')} /
            <span class="english">To be completed by the debtor</span>
        </div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">${_(u'Nom(s) del(s) deutor(s) / (titulars del compte de càrrec)')} /<span class="english">Debtor’s name</span></p>
            <p class="entrada">${d['debtor_name']}</p></div>
            <div class="parella"><p class="label">${_(u'Adreça del deutor')} /<span class="english">Address of the debtor</span></p>
            <p class="entrada">${d['debtor_address']}</p></div>
            <div class="parella"><p class="label">${_(u'Codi postal - Població - Província')} /<span class="english">Postal code - City - Town</span></p>
            <p class="entrada">${d['debtor_province']}</p></div>
            <div class="parella"><p class="label">${_(u'País del deutor')} /<span class="english">Country of the debtor</span></p>
            <p class="entrada">${d['debtor_country']}</p></div>
            <div class="parella"><p class="label">${_(u'Swift BIC')} /<span class="english">Swift BIC (puede contener 8 u 11 posiciones) / Swift BIC (up to 8 or 11 characters)</span></p>
            <p class="entrada entrada-alta">${d['swift']}</p></div>
            <div class="parella"><p class="label">${_(u'Número de compte - IBAN')} /<span class="english">Account number - IBAN</span></p>
            <p class="entrada entrada-alta">${d['debtor_iban_print']}</p></div>
            <p class="english">${_(u'A Espanya l’IBAN consta de 24 posicions començant sempre per ES')} / Spanish IBAN of 24 positions always starting ES</p>
            <div>
                <div class="parella"><p class="label">${_(u'Tipus de pagament')} /<span class="english">Type of payment</span>:</p>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${d['recurring']}>${_(u'Pagament periòdic')} /<span class="english">Recurrent payment</span>
                </label>
                <label  class="entrada-label">
                    <input type="checkbox" name="optradio" ${d['single_payment']}>${_(u'Pagament únic')} /<span class="english">One-off payment</span>
                </label>
            </div>
            <div class="parella"><p class="label">${_(u'Data – Localitat on es realitza la signatura')} /<span class="english">Date - location in which you are signing</span>:</p>
            <p class="entrada">${d['sign_date']} - ${d['debtor_city']}</p></div>
            <div class="parella"><p class="label">${_(u'Signatura del deutor')} /<span class="english">Signature of the debtor</span>:</p>
            <p class="entrada entrada-molt-alta"></p></div>
        </div>
    </div>
    <div class="last">
        % if d['is_business']:
        <p class="spanish centered">
            ${_(u'TOTS ELS CAMPS HAN DE SER OMPLERTS OBLIGATÒRIAMENT.')}
            ${_(u'UNA VEGADA FIRMADA AQUESTA ORDRE DE DOMICILIACIÓ HA DE SER ENVIADA AL CREDITOR PER LA SEVA CUSTÒDIA.')}
            ${_(u'L’ENTITAT DEL DEUTOR REQUEREIX L’AUTORITZACIÓ D’AQUEST PRÈVIA AL CÀRREC EN COMPTE DELS MANDATS B2B.')}
            ${_(u'EL DEUTOR PODRÀ GESTIONAR AQUESTA AUTORITZACIÓ AMB ELS MITJANS QUE LA SEVA ENTITAT POSI A LA SEVA DISPOSICIÓ.')}
            <br>
        <p class="english centered">ALL GAPS ARE MANDATORY. ONCE THIS MANDATE HAS BEEN SIGNED MUST BE SENT TO CREDITOR FOR STORAGE. NEVERTHELESS, THE BANK OF DEBTOR REQUIRES DEBTOR’S AUTHORIZATION
            BEFORE DEBITING B2B DIRECT DEBITS IN THE ACCOUNT. THE DEBTOR WILL BE ABLE TO MANAGE THE MENTIONED AUTHORIZATION THROUGH THE MEANS PROVIDED BY HIS BANK.</p>
        </p>
        % else:
        <p class="spanish centered">
            ${_(u'TOTS ELS CAMPS HAN DE SER OMPLERTS OBLIGATÒRIAMENT.')}

            ${_(u'UNA VEGADA FIRMADA AQUESTA ORDRE DE DOMICILIACIÓ HA DE SER ENVIADA AL CREDITOR PER LA SEVA CUSTÒDIA.')}
            <br>
        </p>
        <p class="english centered">ALL GAPS ARE MANDATORY. ONCE THIS MANDATE HAS BEEN SIGNED MUST BE SENT TO CREDITOR FOR STORAGE.</p>
        % endif
    </div>
</div>
