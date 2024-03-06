<%page args="d" />
% if d.is_visible:
  <style>
  <%include file="simplified_enviromental_impact.css" />
  </style>
    <div class="sei_box">
      <h1>${_(u"Origen de l'electricitat de la comercialitzadora. %s") %d.som.year}</h1>
      <p class="sei_subtitle">${_(u"Som Energia SCCL")}</p>
      <div class="sei_renewable_img">
        <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/simplified_enviromental_impact/grafic-factura-100xcent-renovable.png" width="345px"/>
      </div>
      <div class="sei_table_l">
      <table>
        <thead>
          <td>${_(u"Origen")}</td>
          <td>${_(u"Som Energia")}</td>
          <td>${_(u"Mix generació<br>nacional")}</td>
        </thead>
        <tr>
          <td>${_(u"Renovable")}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.som.renovable, digits=1))}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.mitjana.renovable, digits=1))}</td>
        </tr>
        <tr>
          <td>${_(u"Cogen Alta Eficiència")}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.som.cae, digits=1))}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.mitjana.cae, digits=1))}</td>
        </tr>
        <tr>
          <td>${_(u"CC Gas Natural")}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.som.gasNatural, digits=1))}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.mitjana.gasNatural, digits=1))}</td>
        </tr>
        <tr>
          <td>${_(u"Carbó")}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.som.carbo, digits=1))}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.mitjana.carbo, digits=1))}</td>
        </tr>
        <tr>
          <td>${_(u"Fuel Gas")}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.som.fuelGas, digits=1))}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.mitjana.fuelGas, digits=1))}</td>
        </tr>
        <tr>
          <td>${_(u"Nuclear")}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.som.nuclear, digits=1))}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.mitjana.nuclear, digits=1))}</td>
        </tr>
        <tr>
          <td>${_(u"Altres no renovables")}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.som.altres, digits=1))}</td>
          <td class="sei_cell" style="padding-right: 40px;">${_(u"%s %%") %(formatLang(d.mitjana.altres, digits=1))}</td>
        </tr>
    </table>
    </div>
    </div>
    <div class="sei_box">
      <h1>${_(u"Impacte ambiental de Som Energia. %s") %d.som.year}</h1>
      <p>${_(u"La lletra 'A' correspon al mínim impacte ambiental, la lletra 'D' a la mitjana de generació nacional i la 'G' al màxim impacte ambiental.")}</p>
      <table class="sei_table_r">
        <tr>
          <td>
          <div>${_(u'Emissions de CO<sub>2</sub> equivalents')}</div>
          <div><strong>${_(u'Som Energia')}</strong></div>
          </td>
          <td>
          <div>${_(u'Residus Radioactius Alta Activitat')}</div>
          <div><strong>${_(u'Som Energia')}</strong></div>
          </td>
        </tr>
          <tr>
          <td>
            <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/simplified_enviromental_impact/grafic-factura-impacte-ambiental.png" width="170px"/>
          </td>
          <td>
            <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/simplified_enviromental_impact/grafic-factura-impacte-ambiental.png" width="170px"/>
          </td>
          </tr>
          <tr>
          <td>
            <div class="sei_box_noborder">
              <table>
                <tr>
                  <td>${_(u'Emissions CO<sub>2</sub> eq. (g/kWh)')}</td>
                  <td class="alignright">${_(u"%s") %(formatLang(d.som.emisionCo2, digits=0))}</td>
                </tr>
                <tr>
                  <td>${_(u"Mitjana Nacional (g/kWh)")} </td>
                  <td class="alignright">${_(u"%s") %(formatLang(d.mitjana.emisionCo2, digits=0))}</td>
                </tr>
              </table>
            </div>
          </td>
          <td>
            <div class="sei_box_noborder">
              <table>
                <tr>
                  <td>${_(u"Residus radioactius (&micro;g/kWh)")}</td>
                  <td class="alignright">${_(u"%s") %(formatLang(d.som.residuRadio, digits=0))}</td>
                </tr>
                <tr>
                  <td>${_(u"Mitjana Nacional (&micro;g/kWh)")}</td>
                  <td class="alignright">${_(u"%s") %(formatLang(d.mitjana.residuRadio, digits=0))}</td>
                </tr>
              </table>
            </div>
          </td>
        </tr>
      </table>
      <p class="sei_info">${_(u"Més informació sobre l'origen de la seva electricitat a")}&nbsp; &nbsp;<a href="https://gdo.cnmc.es/">https://gdo.cnmc.es</a></p>
    </div>
% endif
