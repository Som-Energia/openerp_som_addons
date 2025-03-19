<%page args="elec_info" />
% if elec_info.is_visible:
    <style>
    <%include file="electricity_information.css" />
    </style>
    <div class="elect_information">
        <h1>${_(u"INFORMACIÓ DE L'ELECTRICITAT")}</h1>
        <p style="line-height: 1.0;">
            ${_(u"L'electricitat que entra a les nostres llars ens arriba a través de la xarxa de distribució, l'electricitat que hi circula prové "
                u"de diferents fonts, però utilitzant el sistema de certificats de garantia d'origen que emet la CNMC, a Som Energia podem garantir que "
                u"el volum d'electricitat que comercialitzem prové 100% de fonts renovables.")}<br />
        </p>
        <p style="line-height: 1.0;">
            ${_(u"En el gràfic següent mostrem el desglossament de la barreja de tecnologies de producció nacional per poder comparar el percentatge de "
                u"l'energia produïda a escala nacional amb el percentatge d'energia venuda a través de la nostra cooperativa.")}<br />
        </p>
        <br />
        <hr />
        <p style="margin: 0px 0px;font-size: 1.5em; font-weight: 900">${_(u"ORIGEN DE L'ELECTRICITAT")}</p>
        <hr />
        <div class="mix">
            <div class="mix_som">
                <div class="titol" style="width: 100%"><span>${_("Mix Som Energia, SCCL")}</span></div>
                <div class="graf" style="text-align:center;width: 100%">
                    <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/electricity_information/${elec_info.mix_image_som_energia}"/>
                </div>
                <div class="peu">&nbsp;</div>
            </div>
            <div class="mix_esp">
                <div class="titol" style="width: 100%;"><span>${_(u"Mix producció en el sistema elèctric espanyol {year}").format(year=elec_info.year_graph)}</span></div>
                <div class="graf" style="text-align:center; width: 100%">
                    <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/electricity_information/${elec_info.mix_image_rest}"/>
                </div>
                %if elec_info.is_inport:
                    <div class="peu"><p>${_(u"El sistema elèctric espanyol ha importat un {}% de producció neta total").format(formatLang(elec_info.inport_export_value, digits=1))}</p></div>
                %else:
                    <div class="peu"><p>${_(u"El sistema elèctric espanyol ha exportat un {}% de producció neta total").format(formatLang(elec_info.inport_export_value, digits=1))}</p></div>
                %endif
            </div>
        </div>
        <div class="mix_taula">
            <table>
                <thead>
                    <tr>
                        <th>${_(u"Origen")}</th><th style="width: 30%">Som Energia, SCCL</th><th style="width: 30%">${_(u"Mix producció en el sistema elèctric espanyol {year}").format(year=elec_info.year_graph)}</th>
                    </tr>
                </thead>
                <tbody>
                <tr>
                    <td>${_(u"Renovable")}</td><td>${elec_info.renovable.som_energia}</td><td>${elec_info.renovable.mix}</td>
                </tr>
                <tr>
                    <td>${_(u"Cogeneració alta eficiència")}</td><td>${elec_info.high_effic_cogener.som_energia}</td><td>${elec_info.high_effic_cogener.mix}</td>
                </tr>
                <tr>
                    <td>${_(u"Cogeneració")}</td><td>${elec_info.cogener.som_energia}</td><td>${elec_info.cogener.mix}</td>
                </tr>
                <tr>
                    <td>${_(u"CC Gas natural")}</td><td>${elec_info.cc_nat_gas.som_energia}</td><td>${elec_info.cc_nat_gas.mix}</td>
                </tr>
                <tr>
                    <td>${_(u"Carbó")}</td><td>${elec_info.coal.som_energia}</td><td>${elec_info.coal.mix}</td>
                </tr>
                <tr>
                    <td>${_(u"Fuel/Gas")}</td><td>${elec_info.fuel_gas.som_energia}</td><td>${elec_info.fuel_gas.mix}</td>
                </tr>
                <tr>
                    <td>${_(u"Nuclear")}</td><td>${elec_info.nuclear.som_energia}</td><td>${elec_info.nuclear.mix}</td>
                </tr>
                <tr>
                    <td>${_(u"Altres")}</td><td>${elec_info.others.som_energia}</td><td>${elec_info.others.mix}</td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
% endif
