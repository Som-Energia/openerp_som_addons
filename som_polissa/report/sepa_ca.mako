## -*- encoding: utf-8 -*-
<%def name="sepa_ca(data, page_break)">
<div class="extern margin50${' mandate-page' if page_break else ''}">
    <div>
        <img id="logo" width="105px" src="data:image/jpeg;base64,${data['company_logo']}">
        <div class="centered title">
            %if data['is_business']:
                <h1>Ordre de domiciliació de dèbit directe SEPA B2B</h1>
            %else:
                <h1>Ordre de domiciliació de dèbit directe SEPA</h1>
            %endif
        </div>
    </div>
    <div>
        <div class="centered blau">A emplenar pel creditor</div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Referència de l'ordre de domiciliació</p>
            <p class="entrada">${data['order_reference']}</p></div>
            <div class="parella"><p class="label">Identificador del creditor</p>
            <p class="entrada">${data['creditor_code']}</p></div>
            <div class="parella"><p class="label">Nom del creditor</p>
            <p class="entrada">${data['creditor_name']}</p></div>
            <div class="parella"><p class="label">Adreça</p>
            <p class="entrada">${data['creditor_address']}</p></div>
            <div class="parella"><p class="label">Província</p>
            <p class="entrada">${data['creditor_province']}</p></div>
            <div class="parella"><p class="label">País</p>
            <p class="entrada">${data['creditor_country']}</p></div>
        </div>
    </div>
    <div>
        %if data['is_business']:
            <p class="margin20 normal-text">
            Mitjançant la signatura d'aquesta ordre de domiciliació, el deutor autoritza (A) el creditor a enviar instruccions a l'entitat del deutor perquè carregui imports al seu compte i (B) l'entitat a efectuar els càrrecs al seu compte seguint les instruccions del creditor. Aquesta ordre de domiciliació està prevista exclusivament per a operacions entre empreses i/o autònoms. El deutor no té dret que la seva entitat li reemborsi l'import un cop s'hagi efectuat el càrrec en compte, però pot sol·licitar a la seva entitat que no efectuï el càrrec al compte fins a la data de venciment. Pot obtenir informació detallada sobre el procediment a la seva entitat financera.
            </p>
        %else:
            <p class="margin20">
            Mitjançant la signatura d'aquesta ordre de domiciliació, el deutor autoritza (A) el creditor a enviar instruccions a l'entitat del deutor perquè carregui imports al seu compte i (B) l'entitat a efectuar els càrrecs al seu compte seguint les instruccions del creditor. Com a part dels seus drets, el deutor té dret al reemborsament per part de la seva entitat en els termes i les condicions del contracte subscrit amb aquesta. La sol·licitud de reemborsament s'haurà d'efectuar dins de les vuit setmanes següents a la data del càrrec en compte. Pot obtenir informació addicional sobre els seus drets a la seva entitat financera.
            </p>
        %endif
    </div>
    <div>
        <div class="centered blau">A emplenar pel deutor</div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Nom del deutor/s</p>
            <p class="entrada">${data['debtor_name']}</p></div>
            <div class="parella"><p class="label">Adreça del deutor</p>
            <p class="entrada">${data['debtor_address']}</p></div>
            <div class="parella"><p class="label">Província</p>
            <p class="entrada">${data['debtor_province']}</p></div>
            <div class="parella"><p class="label">País del deutor</p>
            <p class="entrada">${data['debtor_country']}</p></div>
            <div class="parella"><p class="label">Swift BIC / <span class="small-text">Swift BIC (pot contenir 8 o 11 posicions)</span></p>
            <p class="entrada entrada-alta">${data['swift']}</p></div>
            <div class="parella"><p class="label">Número de compte - IBAN</p>
            <p class="entrada entrada-alta">${data['debtor_iban_print']}</p></div>
            <p class="small-text">A Espanya l'IBAN consta de 24 posicions i comença sempre per ES</p>
            <div class="parella">
                <p class="label">Tipus de pagament:</p>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['recurring']}>Pagament recurrent
                </label>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['single_payment']}>Pagament únic
                </label>
            </div>
            <div class="parella"><p class="label">Data - Localitat:</p>
            <p class="entrada">${data['sign_date']} - ${data['creditor_city']}</p></div>
            <div class="parella"><p class="label">Signatura del deutor:</p>
            <p class="entrada entrada-molt-alta"></p></div>
        </div>
    </div>
    <div class="last">
        %if data['is_business']:
            <p class="normal-text centered">
                TOTS ELS CAMPS S'HAN D'EMPLENAR OBLIGATÒRIAMENT.
                UN COP SIGNADA, AQUESTA ORDRE DE DOMICILIACIÓ S'HA D'ENVIAR AL CREDITOR PERQUÈ LA CUSTODIÏ.
                L'ENTITAT DEL DEUTOR REQUEREIX L'AUTORITZACIÓ PRÈVIA D'AQUEST ABANS DE CARREGAR ELS DÈBITS DIRECTES B2B AL COMPTE.
                EL DEUTOR PODRÀ GESTIONAR AQUESTA AUTORITZACIÓ MITJANÇANT ELS CANALS QUE LA SEVA ENTITAT POSI A LA SEVA DISPOSICIÓ.
                <br>
            </p>
        %else:
            <p class="normal-text centered">
                TOTS ELS CAMPS S'HAN D'EMPLENAR OBLIGATÒRIAMENT.
                UN COP SIGNADA, AQUESTA ORDRE DE DOMICILIACIÓ S'HA D'ENVIAR AL CREDITOR PERQUÈ LA CUSTODIÏ.
                <br>
            </p>
        %endif
    </div>
</div>
</%def>
