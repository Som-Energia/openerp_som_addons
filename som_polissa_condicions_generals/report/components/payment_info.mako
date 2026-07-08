<%def name="payment_info(titular)">
    % if titular['bank'] or titular['is_recurrent_card_payment']:
    <div class="styled_box">
        <h5> ${_(u"DADES DE PAGAMENT")} </h5>
        <div class="dades_pagament">
            % if titular['is_recurrent_card_payment']:
            <div class="iban"><b>${_(u"Nº de targeta: **** **** ****")}</b> &nbsp ${titular['printable_card_number']}</div>
            % else:
            <div class="iban"><b>${_(u"Nº de compte bancari (IBAN): **** **** **** ****")}</b> &nbsp ${titular['printable_iban']}</div>
            % endif
        </div>
    </div>
    % endif
</%def>
