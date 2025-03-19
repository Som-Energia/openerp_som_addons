<%page args="energy" />
<style>
<%include file="energy_consumption_graphic.css" />
</style>
<script>
var factura_id = ${energy.fact_id}
var data_consum = ${energy.historic_json}
var es30 = ${len(energy.periodes_a)>=3 and 'true' or 'false'}
var esgran = ${energy.is_6X and 'true' or 'false'}
</script>
<div class="chart_consum_container${len(energy.periodes_a)>=3 and '_big' or ''}">
    <div class="chart_consum" id="chart_consum_${energy.fact_id}"></div>
    <div class="chart_estadistica">
        <p>
            ${(_(u"La despesa mitjana diària en els últims %.0f mesos (%s dies) ha estat de <b>%s</b> €, que corresponen a <b>%s</b> kWh/dia.")
                % (energy.average_30_days, energy.historic_dies, formatLang(energy.total_historic_eur_dia), formatLang(energy.total_historic_kw_dia) ))}<br />
            ${_(u"L'electricitat utilitzada durant el darrer any: <b>%s</b> kWh.") % formatLang(energy.total_any, digits=0)}
        </p>
    </div>
</div>
<script src="${addons_path}/giscedata_facturacio_comer_som/report/components/energy_consumption_graphic/energy_consumption_graphic.js"></script>
