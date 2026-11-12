<%page args="energy" />
<style>
<%include file="energy_consumption_graphic_td.css" />
</style>
<script>
var factura_id = ${energy.fact_id}
var data_consum = ${energy.historic_json}
var esgran = ${energy.is_big and 'true' or 'false'}
var average_text = "${energy.average_text}"
</script>
<div class="chart_consum_container_big">
    <div class="chart_consum" id="chart_consum_${energy.fact_id}"></div>
    <div class="chart_estadistica">
        <p>
            ${(_(u"La despesa mitjana diària en els últims %.0f mesos (%s dies) ha estat de <b>%s</b> €, que corresponen a <b>%s</b> kWh/dia.")
                % (energy.average_30_days, energy.historic_dies, formatLang(energy.total_historic_eur_dia), formatLang(energy.total_historic_kw_dia) ))}<br />
            ${_(u"L'electricitat utilitzada durant el darrer any ha estat de <b>%s</b> kWh.") % formatLang(energy.total_any, digits=0)}<br />
            % if energy.required_max_requested_powers:
                % if energy.max_requested_powers:
                    <%
                      pot_p1 = ' '
                      pot_p2 = ' '
                      if len(energy.max_requested_powers) == 2:
                        pot_p1 = energy.max_requested_powers[0]['potencia']
                        pot_p2 = energy.max_requested_powers[1]['potencia']
                      elif energy.max_requested_powers[0]['periode'] == 'P1':
                        pot_p1 = energy.max_requested_powers[0]['potencia']
                      else:
                        pot_p2 = energy.max_requested_powers[0]['potencia']
                    %>
                    ${(_(u"La potència màxima que has fet servir en el període que va del %s fins al %s és de: Punta: <b><i>%s</i></b> kW - Vall: <b><i>%s</i></b> kW (últimes dades rebudes per l’empresa distribuïdora)")
                    % (energy.max_requested_powers[0]['data_inici'], energy.max_requested_powers[0]['data_final'], pot_p1, pot_p2))}  <br />
                % else:
                    ${_("Potència màxima demandada: (ho sentim, %s encara no ens ha facilitat aquestes dades).") % (energy.distri_name)} <br />
                % endif
            % endif
            % if energy.show_mean_zipcode_consumption:
                % if energy.mean_zipcode_consumption:
                    ${(_(u"El consum mitjà de la teva zona (CP %s) durant l'últim mes ha estat de <b>%s</b> kWh.") % (energy.zipcode, formatLang(energy.mean_zipcode_consumption, digits=2)))} <br />
                % else:
                    ${(_(u"Ho sentim, %s no ens ha facilitat el consum mitjà de la teva zona (CP %s) de l’últim mes.") % (energy.distri_name, energy.zipcode))} <br />
                % endif
            % endif
        </p>
    </div>
</div>
<script src="${addons_path}/giscedata_facturacio_comer_som/report/components/energy_consumption_graphic_td/energy_consumption_graphic_td.js"></script>
