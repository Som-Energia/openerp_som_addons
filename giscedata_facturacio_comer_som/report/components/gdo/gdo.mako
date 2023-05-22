<%page args="gdo" />
<style>
<%include file="gdo.css" />
</style>
    <div class="certificate_origin">
        <h1>${_(u"DETALL DELS CERTIFICATS DE GARANTIA D'ORIGEN PER A SOM ENERGIA")}</h1>
        <div class="cert_orig_info">
            <div class="cert_orig_taula">
                <table>
                    <thead>
                    <tr>
                        <th>${_(u"Font renovable")}</th><th>${_(u"Energia MWh")}</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td>${_(u"Eòlica")}</td><td>${formatLang(gdo.wind_power, digits=0)}</td>
                    </tr>
                    <tr>
                        <td>${_(u"Solar fotovoltaica")}</td><td>${formatLang(gdo.photovoltaic, digits=0)}</td>
                    </tr>
                    <tr>
                        <td>${_(u"Minihidràulica")}</td><td>${formatLang(gdo.hydraulics, digits=0)}</td>
                    </tr>
                    %if gdo.biogas:
                        <tr>
                            <td>${_(u"Biogàs")}</td><td>${formatLang(gdo.biogas, digits=0)}</td>
                        </tr>
                    %endif
                    %if gdo.biomassa:
                        <tr>
                            <td>${_(u"Biomassa")}</td><td>${formatLang(gdo.biomassa, digits=0)}</td>
                        </tr>
                    %endif
                    </tbody>
                    <tfoot>
                    <tr>
                        <td>${_(u"TOTAL")}</td><td>${formatLang(gdo.total, digits=0)}</td>
                    </tr>
                    </tfoot>
                </table>
            </div>
            ${_(u"Pots veure l'origen dels certificats de garantia d'origen en l'enllaç següent:")}<br/><a href="http://bit.ly/GdO15${gdo.lang}")}>http://bit.ly/GdO15${gdo.lang}</a>
        </div>
        <div class="cert_orig_grafic">
            <img class="orig" src="${addons_path}/giscedata_facturacio_comer_som/report/components/gdo/${gdo.graph}"/>
        </div>
    </div>
