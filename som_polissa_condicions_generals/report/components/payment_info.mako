<%def name="payment_info(titular)">
    % if titular['bank']:
    <div class="styled_box">
        <h5> ${_(u"DADES DE PAGAMENT")} </h5>
        <div class="dades_pagament">
            <div class="iban"><b>${_(u"Nº de compte bancari (IBAN): **** **** **** ****")}</b> &nbsp ${titular['printable_iban']}</div>
        </div>
    </div>
    % endif
</%def>
