<%page args="d" />
<style>
<%include file="simplified_enviromental_impact.css" />
</style>
  <div class="sei_box">
    <h1>${_(u"Origen de l'electricitat de la comercialitzadora. 2021")}</h1>
    <p class="sei_subtitle">${_(u"Som Energia SCCL")}</p>
    <div class="sei_renewable_img">
      <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/simplified_enviromental_impact/simplified_enviromental_impact_renewable.png" width="245px"/>
    </div>
    <div class="sei_table_l">
    <table>
    	<thead>
        <td>${_(u"Origen")}</td>
        <td>${_(u"Som Energia")}</td>
        <td>${_(u"Mix generació nacional")}</td>
    	</thead>
      <tr>
        <td>${_(u"Renovable")}</td>
        <td class="sei_cell">45,2%</td>
        <td class="sei_cell">40,0%</td>
      </tr>
      <tr>
        <td>${_(u"Cogen Alta Eficiència")}</td>
        <td class="sei_cell">4,8%</td>
        <td class="sei_cell">4,9%</td>
      </tr>
      <tr>
        <td>${_(u"CC Gas Natural")}</td>
        <td class="sei_cell">15,3%</td>
        <td class="sei_cell">21,5%</td>
      </tr>
      <tr>
        <td>${_(u"Carbó")}</td>
        <td class="sei_cell">7,7%</td>
        <td class="sei_cell">1,9%</td>
      </tr>
      <tr>
        <td>${_(u"Fuel Gas")}</td>
        <td class="sei_cell">7,1%</td>
        <td class="sei_cell">2,2%</td>
      </tr>
      <tr>
        <td>${_(u"Nuclear")}</td>
        <td class="sei_cell">14,9%</td>
        <td class="sei_cell">21,8%</td>
      </tr>
      <tr>
        <td>${_(u"Altres no renovables")}</td>
        <td class="sei_cell">5,0%</td>
        <td class="sei_cell">7,7%</td>
      </tr>
	</table>
  </div>
  </div>
  <div class="sei_box">
     <h1>${_(u"Impacte ambiental de la seva comercialitzadora. 2021")}</h1>
     <p>${_(u"La lletra 'A' correspon al mínim impacte ambiental, la lletra 'D' a la mitjana de generació nacional i la 'G' al màxim impacte ambiental.")}</p>
     <table class="sei_table_r">
    	<tr>
        <td>
        <div>${_(u'Emisions de CO<sub>2</sub> equivalents')}</div>
        <div><strong>${_(u'Som Energia')}</strong></div>
        </td>
        <td>
        <div>${_(u'Residus Radioactius Alta Activitat')}</div>
        <div><strong>${_(u'Som Energia')}</strong></div>
        </td>
    	</tr>
        <tr>
        <td>
           <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/simplified_enviromental_impact/simplified_enviromental_impact_som.png" width="120px"/>
        </td>
        <td>
           <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/simplified_enviromental_impact/simplified_enviromental_impact_som.png" width="120px"/>
        </td>
        </tr>
        <tr>
        <td>
        <div>${_(u'Emisions CO<sub>2</sub> eq. (g/kWh)')}<b>145</b></div>
        <div>${_(u"Mitjana Nacional (g/kWh)")} <b>204</b></div>
        </td>
        <td>
        <div>${_(u"Residus radioactius (&micro;g/kWh)")} <strong>483</strong></div>
        <div>${_(u"Mitjana Nacional (&micro;g/kWh)")} <strong>530</strong></div> 
        </td>
        </tr>
    </table>
    <p class="sei_info">${_(u"Més informació sobre l'origen de la seva electricitat a ")} <a href="https://gdo.cnmc.es/"></a>https://gdo.cnmc.es</p>
  </div>



