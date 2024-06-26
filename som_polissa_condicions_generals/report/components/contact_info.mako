<%def name="contact_info(titular, cups)">
    <div class="contact_info">
        <div class="persona_titular styled_box ${"width33" if titular['diferent'] else "width49"}">
            <h5>${_(u"PERSONA TITULAR")}</h5>
            <div class="inside_styled_box">
                <b>${_(u"Nom/Raó social: ")}</b>
                ${titular['client_name']}<br/>
                <b>${_(u"NIF/CIF: ")}</b>
                ${titular['client_vat']}<br/>
                <b>${_(u"Adreça: ")}</b>
                ${titular['street']}<br/>
                <b>${_(u"Codi postal i municipi: ")}</b>
                ${titular['zip']} ${titular['city']}<br/>
                <b>${_(u"Província i país: ")}</b>
                ${titular['state']} ${titular['country']}<br/>
                <b>${_(u"Adreça electrònica: ")}</b>
                ${titular['email']}<br/>
                <b>${_(u"Telèfon: ")}</b>
                ${titular['mobile']}<br/>
                <b>${_(u"Telèfon 2: ")}</b>
                ${titular['phone']}<br/>
            </div>
        </div>

        <div class="dades_subministrament styled_box ${"width33" if titular['diferent'] else "width49"}">
            <h5> ${_(u"DADES DEL PUNT DE SUBMINISTRAMENT")} </h5>

            <div class="inside_styled_box">
                <b>${_(u"Adreça: ")}</b>
                ${cups['direccio']}</br>
                <b>${_(u"Província i país: ")}</b>
                ${cups['provincia']} ${cups['country']}</br>
                <b>${_(u"CUPS: ")}</b>
                ${cups['name']}</br>
                <b>${_(u"CNAE: ")}</b>
                ${cups['cnae']}</br>
                <b>${_(u"Contracte d'accés: ")}</b>
                ${cups['ref_dist']}</br>
                <b>${_(u"Activitat principal: ")}</b>
                ${cups['cnae_des']}</br>
                <b>${_(u"Empresa distribuïdora: ")}</b>
                ${cups['distri']}</br>
                <b>${_(u"Tensió Nominal (V): ")}</b>
                ${cups['tensio']}</br>
            </div>
        </div>

        %if titular['diferent']:
        <div class="dades_de_contacte styled_box ${"width33" if titular['diferent'] else "width49"}">
            <h5> ${_(u"DADES DE CONTACTE")} </h5>
            <div class="inside_styled_box">
                <b>${_(u"Nom/Raó social: ")}</b>
                ${titular['name_envio']}<br/>
                <b>${_(u"Adreça: ")}</b>
                ${titular['street_envio']}<br/>
                <b>${_(u"Codi postal i municipi: ")}</b>
                ${titular['zip_envio']} ${titular['city_envio']}<br/>
                <b>${_(u"Província i país: ")}</b>
                ${titular['state_envio']} ${titular['country_envio']}<br/>
                <b>${_(u"Adreça electrònica: ")}</b>
                ${titular['email_envio']}<br/>
                <b>${_(u"Telèfon: ")}</b>
                ${titular['mobile_envio']}<br/>
                <b>${_(u"Telèfon 2: ")}</b>
                ${titular['phone_envio']}<br/>
            </div>
        </div>
        %endif
    </div>
</%def>
