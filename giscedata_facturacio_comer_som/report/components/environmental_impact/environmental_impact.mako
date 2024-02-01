<%page args="ei" />
% if ei.is_visible:
    <style>
    <%include file="environmental_impact.css" />
    </style>
    <div class="environment_impact">
        <h1>${_(u"IMPACTE AMBIENTAL")}</h1>
        <p class="env_imp_desc">
            ${_(u"L'impacte ambiental de l'electricitat que utilitzem depèn de les fonts de generació que s'utilitzen per a la seva producció.")}
        <br />
            ${_(u"En una escala de A a G (on A indica el mínim impacte ambiental i G el màxim), i tenint en compte que el valor mitjà nacional correspon al nivell D, "
                u"l'energia comercialitzada per Som Energia, SCCL, té els valors següents:")}
        </p>
        <div class="env_imp">
            <div class="env_imp_carbo" >
                <div class="env_titol"><p>${_(u"Emissions de diòxid de carboni ")}<br /><span style="font-weight: 900">Som Energia, SCCL</span></p></div>
                <div class="env_img_lleg">${_(u"Menys diòxid de carboni")}</div>
                <div class="env_img">
                    <img class="a_g" src="${addons_path}/giscedata_facturacio_comer_som/report/components/environmental_impact/environmental_impact_graph.png"/>
                </div>
                <div class="env_mitjana" >
                    <p>${_(u'Mitjana nacional')}<br /><span style="font-weight: 900;">${ei.c02_emissions.national_average}</span></p>
                </div>
                <div class="env_marc">${_(u'Contingut de carboni<br />Quilograms de diòxid de carboni per kWh')}<br /><span style="font-weight: 900;font-size: 1.1em">${ei.c02_emissions.som_energia}</span></div>
                <div class="env_img_lleg">${_(u"Més diòxid de carboni")}</div>
            </div>
        <div class="env_imp_nuclear" >
                <div class="env_titol"><p>${_(u"Residus radioactius d'alta activitat ")}<br /><span style="font-weight: 900">Som Energia, SCCL</span></p></div>
                <div class="env_img_lleg">${_(u"Menys residus radioactius")}</div>
                <div class="env_img">
                    <img class="a_g" src="${addons_path}/giscedata_facturacio_comer_som/report/components/environmental_impact/environmental_impact_graph.png"/>
                </div>
                <div class="env_mitjana">
                    <p>${_(u'Mitjana nacional')}<br /><span style="font-weight: 900;">${ei.radioactive_waste.national_average}</span></p>
                </div>
                <div class="env_marc">${_(u'Residus radioactius<br />Mil·ligrams per kWh')}<br /><span style="font-weight: 900;font-size: 1.1em">${ei.radioactive_waste.som_energia}</span></div>
                <div class="env_img_lleg">${_(u"Més residus radioactius")}</div>
            </div>
        </div>
    </div>
% endif
