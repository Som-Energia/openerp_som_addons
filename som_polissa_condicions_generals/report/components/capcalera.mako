<%def name="capcalera(polissa)">
    <div id="capcelera">
        <div id="logo_capcelera">
            <img id="logo" src="${addons_path}/som_polissa_condicions_generals/report/assets/logo2.png"/>
        </div>
        <div id="address_capcelera">
            <b>${_(u"Som Energia, SCCL")}</b><br/>
            <b>${_(u"CIF:")}</b> ${_(u" F55091367")}<br/>
            <b>${_(u"Domicili:")}</b> ${_(u" C/Riu Güell, 68<br/>17005, Girona")}<br/>
            <b>${_(u"Adreça electrònica:")} </b> ${_(u" info@somenergia.coop")}
        </div>
        <div id="dades_capcelera">
            <div id="titol_dades">
                <h3>${_(u"DADES DEL CONTRACTE")}</h3>
            </div>
            <div id="bloc_dades_capcelera">
                <b>${_(u"Contracte núm.: ")}</b> ${polissa['name']}<br/>
                <b>${_(u"Data d'inici del subministrament: ")}</b>
                %if polissa['state'] == 'esborrany':
                    &nbsp;
                %else:
                    ${polissa['data_inici']}
                %endif
                <br/>
                <b>${_(u"Data de renovació del subministrament: ")}</b>
                %if polissa['state'] == 'esborrany':
                    &nbsp;
                %else:
                    ${polissa['data_final']}
                %endif
                <br/>
            </div>
        </div>
    </div>
    <div id="titol">
        <h2>${_(u"CONDICIONS PARTICULARS DEL CONTRACTE DE SUBMINISTRAMENT D'ENERGIA ELÈCTRICA")}</h2>
    </div>
    %if polissa['state'] == 'esborrany' and not polissa['lead']:
        <div class="esborrany_warning">
            <img src="${addons_path}/som_polissa_condicions_generals/report/assets/warning_icon.png"/>
            <h2>
                ${_(u"LES DADES D'AQUEST CONTRACTE ESTAN PENDENTS DE VALIDACIÓ.")}
            </h2>
            <h3>
                ${_(u"Les tarifes que s’aplicaran seran les vigents al moment d'activar el contracte.")}
            </h3>
        </div>
    %endif
</%def>
