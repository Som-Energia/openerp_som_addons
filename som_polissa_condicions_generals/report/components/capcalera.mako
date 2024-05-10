<%def name="capcalera(polissa)">
    <div id="capcelera">
        <div id="logo_capcelera">
            <img id="logo" src="${addons_path}/som_polissa_condicions_generals/report/assets/logo.png"/>
        </div>
        <div id="address_capcelera">
            <b>${_(u"Som Energia, SCCL")}</b><br/>
            <b>${_(u"CIF:")}</b> ${_(u" F55091367")}<br/>
            <b>${_(u"Domicili:")}</b> ${_(u" C/Pic de Peguera, 9 (1a planta)<br/>17003, Girona")}<br/>
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
</%def>