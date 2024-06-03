<%def name="payment_info(polissa)">
    % if polissa['bank']:
    <div class="styled_box">
        <h5> ${_("DADES DE PAGAMENT")} </h5>
        <div class="dades_pagament">
            <div class="iban"><b>${_(u"Nº de compte bancari (IBAN): **** **** **** ****")}</b> &nbsp ${polissa['printable_iban']}</div>
        </div>
    </div>
    % endif
</%def>
