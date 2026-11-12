## -*- encoding: utf-8 -*-
<%def name="sepa_es(data, page_break)">
<div class="extern margin50${' mandate-page' if page_break else ''}">
    <div>
        <img id="logo" width="105px" src="data:image/jpeg;base64,${data['company_logo']}">
        <div class="centered title">
            %if data['is_business']:
                <h1>Orden de domiciliación de adeudo directo SEPA B2B</h1>
            %else:
                <h1>Orden de domiciliación de adeudo directo SEPA</h1>
            %endif
        </div>
    </div>
    <div>
        <div class="centered blau">A cumplimentar por el acreedor</div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Referencia de la orden de domiciliación</p>
            <p class="entrada">${data['order_reference']}</p></div>
            <div class="parella"><p class="label">Identificador del acreedor</p>
            <p class="entrada">${data['creditor_code']}</p></div>
            <div class="parella"><p class="label">Nombre del acreedor</p>
            <p class="entrada">${data['creditor_name']}</p></div>
            <div class="parella"><p class="label">Dirección</p>
            <p class="entrada">${data['creditor_address']}</p></div>
            <div class="parella"><p class="label">Provincia</p>
            <p class="entrada">${data['creditor_province']}</p></div>
            <div class="parella"><p class="label">País</p>
            <p class="entrada">${data['creditor_country']}</p></div>
        </div>
    </div>
    <div>
        %if data['is_business']:
            <p class="margin20 normal-text">
            Mediante la firma de esta orden de domiciliación, el deudor autoriza (A) al acreedor a enviar instrucciones a la entidad del deudor para adeudar su cuenta y (B) a la entidad para efectuar los adeudos en su cuenta siguiendo las instrucciones del acreedor. Esta orden de domiciliación está prevista para operaciones exclusivamente entre empresas y/o autónomos. El deudor no tiene derecho a que su entidad le reembolse una vez que se haya realizado el cargo en cuenta, pero puede solicitar a su entidad que no efectúe el adeudo en la cuenta hasta la fecha debida. Podrá obtener información detallada del procedimiento en su entidad financiera.
            </p>
        %else:
            <p class="margin20">
            Mediante la firma de esta orden de domiciliación, el deudor autoriza (A) al acreedor a enviar instrucciones a la entidad del deudor para adeudar su cuenta y (B) a la entidad para efectuar los adeudos en su cuenta siguiendo las instrucciones del acreedor. Como parte de sus derechos, el deudor está legitimado al reembolso por su entidad en los términos y condiciones del contrato suscrito con la misma. La solicitud de reembolso deberá efectuarse dentro de las ocho semanas que siguen a la fecha de adeudo en cuenta. Puede obtener información adicional sobre sus derechos en su entidad financiera.
            </p>
        %endif
    </div>
    <div>
        <div class="centered blau">A cumplimentar por el deudor</div>
        <div class="intern margin50 full-width">
            <div class="parella"><p class="label">Nombre del deudor/es</p>
            <p class="entrada">${data['debtor_name']}</p></div>
            <div class="parella"><p class="label">Dirección del deudor</p>
            <p class="entrada">${data['debtor_address']}</p></div>
            <div class="parella"><p class="label">Provincia</p>
            <p class="entrada">${data['debtor_province']}</p></div>
            <div class="parella"><p class="label">País del deudor</p>
            <p class="entrada">${data['debtor_country']}</p></div>
            <div class="parella"><p class="label">Swift BIC / <span class="small-text">Swift BIC (puede contener 8 u 11 posiciones)</span></p>
            <p class="entrada entrada-alta">${data['swift']}</p></div>
            <div class="parella"><p class="label">Número de cuenta - IBAN</p>
            <p class="entrada entrada-alta">${data['debtor_iban_print']}</p></div>
            <p class="small-text">En España el IBAN consta de 24 posiciones comenzando siempre por ES</p>
            <div class="parella">
                <p class="label">Tipo de pago:</p>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['recurring']}>Pago recurrente
                </label>
                <label class="entrada-label">
                    <input type="checkbox" name="optradio" ${data['single_payment']}>Pago único
                </label>
            </div>
            <div class="parella"><p class="label">Fecha - Localidad:</p>
            <p class="entrada">${data['sign_date']} - ${data['creditor_city']}</p></div>
            <div class="parella"><p class="label">Firma del deudor:</p>
            <p class="entrada entrada-molt-alta"></p></div>
        </div>
    </div>
    <div class="last">
        %if data['is_business']:
            <p class="normal-text centered">
                TODOS LOS CAMPOS HAN DE SER CUMPLIMENTADOS OBLIGATORIAMENTE.
                UNA VEZ FIRMADA ESTA ORDEN DE DOMICILIACIÓN DEBE SER ENVIADA AL ACREEDOR PARA SU CUSTODIA.
                LA ENTIDAD DE DEUDOR REQUIERE AUTORIZACIÓN DE ÉSTE PREVIA AL CARGO EN CUENTA DE LOS ADEUDOS DIRECTOS B2B.
                EL DEUDOR PODRÁ GESTIONAR DICHA AUTORIZACIÓN CON LOS MEDIOS QUE SU ENTIDAD PONGA A SU DISPOSICIÓN.
                <br>
            </p>
        %else:
            <p class="normal-text centered">
                TODOS LOS CAMPOS HAN DE SER CUMPLIMENTADOS OBLIGATORIAMENTE.
                UNA VEZ FIRMADA ESTA ORDEN DE DOMICILIACIÓN DEBE SER ENVIADA AL ACREEDOR PARA SU CUSTODIA.
                <br>
            </p>
        %endif
    </div>
</div>
</%def>
