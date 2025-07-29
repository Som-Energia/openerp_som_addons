<%page args="ad" />
<style>
<%include file="amount_destination_td.css" />
</style>

<script>
var pie_data = [
    {value: ${ad.pie_charges}, name: '${_(u"Càrrecs")}'},
    {value: ${ad.pie_tolls}, name: '${_(u"Peatges de transport i distribució")}'},
    {value: ${ad.pie_renting}, name: '${_(u"Lloguer de comptador")}'},
    {value: ${ad.pie_energy}, name: '${_(u"Energia")}'},
    {value: ${ad.pie_taxes}, name: '${_(u"Impostos aplicats")}'},
];

var dades_reparto = [
    { value: ${float((ad.pie_charges * ad.rep_BOE['d'])/100)}, name: '${_(u"Anualitat del dèficit")}' },
    { value: ${float((ad.pie_charges * ad.rep_BOE['r'])/100)}, name: '${_(u"RECORE: retribució a les renovables, cogeneració i residus")}' },
    { value: ${float((ad.pie_charges * ad.rep_BOE['t'])/100)}, name: '${_(u"Sobrecost de generació a territoris no peninsulars (TNP)")}' },
    { value: ${float((ad.pie_charges * ad.rep_BOE['o'])/100)}, name: '${_(u"Altres costos regulats")}' },
];
</script>
<!-- DESTI DE LA FACTURA -->
    % if ad.is_visible:
        <div class="destination">
            <h1>${_(u"DESTÍ DE L'IMPORT DE LA FACTURA")}</h1>
            % if ad.has_flux:
                <p>${_(u"El destí de l'import de la teva factura sense flux solar, %s euros, és el següent:") % formatLang(ad.amount_total)}</p>
            % else:
                <p>${_(u"El destí de l'import de la teva factura, %s euros, és el següent:") % formatLang(ad.amount_total)}</p>
            %endif
            <div class="chart_desti" id="chart_desti" style="width: 750px; height: 200px"></div>
        </div>
    % endif
<script src="${addons_path}/giscedata_facturacio_comer_som/report/components/amount_destination_td/amount_destination_td.js"></script>
