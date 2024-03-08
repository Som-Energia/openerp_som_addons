<%page args="ad" />
<style>
<%include file="amount_destination_td.css" />
</style>
<%
import json

reparto = { 'r': float((ad.pie_charges * ad.rep_BOE['r'])/100),
            'd': float((ad.pie_charges * ad.rep_BOE['d'])/100),
            't': float((ad.pie_charges * ad.rep_BOE['t'])/100),
            'o': float((ad.pie_charges * ad.rep_BOE['o'])/100)
            }

def add_reparto(l, percent, increment, tag, text, value, y_offset):
    next = min(percent + float(increment), 100.0)
    l.append([[percent, next], tag, text, formatLang(value), y_offset])
    return next

percent = 0.0
dades_reparto = []
percent = add_reparto(dades_reparto, percent, ad.rep_BOE['r'], 'r', _(u"RECORE: retribució a les renovables, cogeneració i residus"), reparto['r'], 15)
percent = add_reparto(dades_reparto, percent, ad.rep_BOE['d'], 'd', _(u"Anualitat del dèficit"), reparto['d'], 15)
percent = add_reparto(dades_reparto, percent, ad.rep_BOE['t'], 't', _(u"Sobrecost de generació a territoris no peninsulars (TNP)"), reparto['t'], 15)
percent = add_reparto(dades_reparto, percent, ad.rep_BOE['o'], 'o', _(u"Altres costos regulats"), reparto['o'], 7)
%>

<script>
var pie_total = ${ad.pie_total};
var pie_data = [{val: ${ad.pie_charges},  perc: 15 ,code: "CHAR"},
                {val: ${ad.pie_tolls},  perc: 15 ,code: "TOLL"},
                {val: ${ad.pie_renting}, perc: 15, code: "RENT"},
                {val: ${ad.pie_energy},  perc: 15 ,code: "ENER"},
                {val: ${ad.pie_taxes},  perc: 15 ,code: "TAX"}
               ];

var pie_etiquetes = {'RENT': {t: ['${formatLang(float(ad.pie_renting))} €','${_(u"Lloguer de comptador")}'], w:89},
                     'TAX': {t: ['${formatLang(float(ad.pie_taxes))} €','${_(u"Impostos aplicats")}'], w:75},
                     'TOLL': {t: ['${formatLang(float(ad.pie_tolls))} €','${_(u"Peatges de transport i distribució")}'], w:130},
                     'CHAR': {t: ['${formatLang(float(ad.pie_charges))} €','${_(u"Càrrecs")}'], w:50},
                     'ENER': {t: ['${formatLang(float(ad.pie_energy))} €','${_(u"Energia")}'], w:35}
                    };
var reparto = ${json.dumps(reparto)}
var dades_reparto = ${json.dumps(dades_reparto)}
</script>
<!-- DESTI DE LA FACTURA -->
    % if ad.is_visible:
        <div class="destination">
            <h1>${_(u"DESTÍ DE L'IMPORT DE LA FACTURA")}</h1>
            <p>${_(u"El destí de l'import de la teva factura, %s euros, és el següent:") % formatLang(ad.amount_total)}</p>
            <div class="chart_desti" id="chart_desti_${ad.factura_id}"></div>
        </div>
    % endif
<script src="${addons_path}/giscedata_facturacio_comer_som/report/components/amount_destination_td/amount_destination_td.js"></script>
