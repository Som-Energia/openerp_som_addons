<%page args="ad" />
<style>
<%include file="amount_destination.css" />
</style>
<%
import json

reparto = { 'i': float((ad.pie_regulats * ad.rep_BOE['i'])/100),
            'c': float((ad.pie_regulats * ad.rep_BOE['c'])/100),
            'o': float((ad.pie_regulats * ad.rep_BOE['o'])/100)
            }

dades_reparto = [
    [[0, float(ad.rep_BOE['i'])], 'i', _(u"Incentius a les energies renovables, cogeneració i residus"), formatLang(reparto['i'])],
    [[float(ad.rep_BOE['i']) , float(ad.rep_BOE['i'] + ad.rep_BOE['c'])], 'c', _(u"Cost de xarxes de distribució i transport"), formatLang(reparto['c'])] ,
    [[float(ad.rep_BOE['i'] + ad.rep_BOE['c']), 100.00], 'o', _(u"Altres costos regulats (inclosa anualitat del dèficit)"), formatLang(reparto['o'])]
    ]
%>
<script>
var pie_total = ${ad.pie_total};
var pie_data = [{val: ${ad.pie_regulats}, perc: 30, code: "REG"},
                {val: ${ad.pie_costos}, perc: 55, code: "PROD"},
                {val: ${ad.pie_impostos},  perc: 15 ,code: "IMP"}
               ];

var pie_etiquetes = {'REG': {t: ['${formatLang(float(ad.pie_regulats))} €','${_(u"Costos regulats")}'], w:100},
                     'IMP': {t: ['${formatLang(float(ad.pie_impostos))} €','${_(u"Impostos aplicats")}'], w:100},
                     'PROD': {t: ['${formatLang(float(ad.pie_costos))} €','${_(u"Costos de producció electricitat")}'], w:150}
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
    % if ad.total_lloguers:
            <p>${_(u"Als imports indicats en el diagrama s'ha d'afegir, si s'escau, el lloguer dels equips de mesura i control: %s €.") % formatLang(ad.total_lloguers)}</p>
    % endif
        </div>
    % endif
<script src="${addons_path}/giscedata_facturacio_comer_som/report/components/amount_destination/amount_destination.js"></script>
