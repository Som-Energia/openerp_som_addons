## -*- coding: utf-8 -*-
<%
import locale
locale.setlocale(locale.LC_NUMERIC,'es_ES.utf-8')
r_obj = objects[0].pool.get('giscedata.facturacio.factura.report')
report_data = r_obj.get_report_data(cursor, uid, objects)
%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
<link rel="stylesheet" href="${addons_path}/giscedata_facturacio_indexada/report/js/c3.min.css">
<link rel="stylesheet" href="${addons_path}/giscedata_facturacio_comer_som/report/giscedata_facturacio_comer_som.css"/>
<script src="${addons_path}/giscedata_facturacio_comer/report/assets/d3.min.js"></script>
</head>
<body>
<%
    ajust_fet = False
    motiu_ajust = ''
%>
<script src="${addons_path}/giscedata_facturacio_comer_som/report/d3.min.js"></script>
<script>
    d3_antic = d3
    window.d3 = null
</script>
<script src="${addons_path}/giscedata_facturacio_indexada/report/js/d3.min.js"></script>
<script src="${addons_path}/giscedata_facturacio_indexada/report/js/c3.min.js"></script>

<script src="${addons_path}/giscedata_facturacio_comer_som/report/echarts5.min.js"></script>

%for comptador_factures, factura in enumerate(objects):
<%
    setLang(factura.lang_partner)
    factura_data = report_data[factura.id]
%>
<%include file="/giscedata_facturacio_comer_som/report/components/lateral_text/lateral_text.mako" args="lt=factura_data.lateral_text" />
<div id="container">

% if factura_data.globals.is_TD: # Factura 2.0TD 3.0TD 6.XTD

    <div class="company_address" style="font-size: .7em;">
        <%include file="/giscedata_facturacio_comer_som/report/components/logo/logo.mako" args="logo=factura_data.logo" />
        <%include file="/giscedata_facturacio_comer_som/report/components/company/company.mako" args="company=factura_data.company" />
    </div>
    <div class="invoice_data">
        <%include file="/giscedata_facturacio_comer_som/report/components/flags/flags.mako" args="flags=factura_data.flags" />
        <%include file="/giscedata_facturacio_comer_som/report/components/invoice_info/invoice_info.mako" args="ii=factura_data.invoice_info" />
    </div>
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_summary_td/invoice_summary_td.mako" args="invs=factura_data.invoice_summary_td" />
    <%include file="/giscedata_facturacio_comer_som/report/components/partner_info/partner_info.mako" args="pi=factura_data.partner_info" />
    <%include file="/giscedata_facturacio_comer_som/report/components/rectificative_banner/rectificative_banner.mako" args="rb=factura_data.rectificative_banner" />
    <!-- LECTURES ACTIVA i GRÀFIC BARRES -->
    <div class="energy_info">
        <h1>${_(u"INFORMACIÓ DE L'ELECTRICITAT UTILITZADA")}</h1>
        <div>
            <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_graphic_td/energy_consumption_graphic_td.mako" args="energy=factura_data.energy_consumption_graphic_td" />
            % if factura_data.globals.is_indexed and factura_data.globals.is_abonadora == False:
                <%include file="/giscedata_facturacio_comer_som/report/components/hourly_curve/hourly_curve.mako" args="hc=factura_data.hourly_curve" />
            % endif
        </div>
    </div>
    <div class="energy_consumption_info">
        <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td/energy_consumption_detail_td.mako" args="id=factura_data.energy_consumption_detail_td" />
    </div>
    <%include file="/giscedata_facturacio_comer_som/report/components/contract_data_td/contract_data_td.mako" args="cd=factura_data.contract_data_td" />
    <%include file="/giscedata_facturacio_comer_som/report/components/emergency_complaints_td/emergency_complaints_td.mako" args="ec=factura_data.emergency_complaints_td" />
    <p style="page-break-after:always"></p>

    <!-- DETALL FACTURA -->
    <div class="invoice_detail">
        <h1>${_(u"DETALL DE LA FACTURA")}</h1>
        <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td/invoice_details_td.mako" args="id=factura_data.invoice_details_td" />
        <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_info_td/invoice_details_info_td.mako" args="id_info=factura_data.invoice_details_info_td" />
    </div>
    <%include file="/giscedata_facturacio_comer_som/report/components/solar_flux_info/solar_flux_info.mako" args="sf=factura_data.solar_flux_info" />
    <%include file="/giscedata_facturacio_comer_som/report/components/cnmc_comparator_qr_link/cnmc_comparator_qr_link.mako" args="comparator=factura_data.cnmc_comparator_qr_link" />
    <%include file="/giscedata_facturacio_comer_som/report/components/amount_destination_td/amount_destination_td.mako" args="ad=factura_data.amount_destination_td" />
    <p style="page-break-after:always"></p>
    <%include file="/giscedata_facturacio_comer_som/report/components/simplified_enviromental_impact/simplified_enviromental_impact.mako" args="d=factura_data.simplified_enviromental_impact" />
    <%include file="/giscedata_facturacio_comer_som/report/components/electricity_information/electricity_information.mako" args="elec_info=factura_data.electricity_information" />
    <%include file="/giscedata_facturacio_comer_som/report/components/environmental_impact/environmental_impact.mako" args="ei=factura_data.environmental_impact" />
    <%include file="/giscedata_facturacio_comer_som/report/components/gdo/gdo.mako" args="gdo=factura_data.gdo" />
    <p style="font-size: .8em; float: right">
    ${_(u"Informació sobre protecció de dades: Les dades personals tractades per gestionar la relació contractual i, si s'escau, remetre informació comercial per mitjans electrònics, es conservaran fins a la fi de la relació, baixa comercial o els terminis de retenció legals. Pots exercir els teus drets a l'adreça postal de Som Energia com a responsable o a somenergia@delegado-datos.com .")}<br />
    </p>

% else: # Factura 20A 20DHA 20DHS 3.0A 6.XA

    <div class="company_address" style="font-size: .7em;">
        <%include file="/giscedata_facturacio_comer_som/report/components/logo/logo.mako" args="logo=factura_data.logo" />
        <%include file="/giscedata_facturacio_comer_som/report/components/company/company.mako" args="company=factura_data.company" />
    </div>
    <div class="invoice_data">
        <%include file="/giscedata_facturacio_comer_som/report/components/flags/flags.mako" args="flags=factura_data.flags" />
        <%include file="/giscedata_facturacio_comer_som/report/components/invoice_info/invoice_info.mako" args="ii=factura_data.invoice_info" />
    </div>
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_summary/invoice_summary.mako" args="invs=factura_data.invoice_summary" />
    <%include file="/giscedata_facturacio_comer_som/report/components/partner_info/partner_info.mako" args="pi=factura_data.partner_info" />
    <%include file="/giscedata_facturacio_comer_som/report/components/rectificative_banner/rectificative_banner.mako" args="rb=factura_data.rectificative_banner" />
    <!-- LECTURES ACTIVA i GRÀFIC BARRES -->
    <div class="energy_info">
        <h1>${_(u"INFORMACIÓ DEL CONSUM ELÈCTRIC")}</h1>
        % if factura_data.globals.is_6x:
            <div class="" style="padding: 10px;">
                <%include file="/giscedata_facturacio_comer_som/report/components/readings_6x/readings_6x.mako" args="readings_6x=factura_data.readings_6x" />
                <div class="column">
                    <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_graphic/energy_consumption_graphic.mako" args="energy=factura_data.energy_consumption_graphic" />
                </div>
            </div>
        % else:
            % if factura_data.globals.num_periodes < 3:
                <div class="energy_child_info">
            % else:
                <div>
            %endif
                <%include file="/giscedata_facturacio_comer_som/report/components/readings_table/readings_table.mako" args="readings=factura_data.readings_table" />
                <%include file="/giscedata_facturacio_comer_som/report/components/meters/meters.mako" args="meters=factura_data.meters,location='up'" />
                <%include file="/giscedata_facturacio_comer_som/report/components/readings_g_table/readings_g_table.mako" args="readings=factura_data.readings_g_table" />
                <%include file="/giscedata_facturacio_comer_som/report/components/readings_text/readings_text.mako" args="readings=factura_data.readings_text" />
            </div>
            % if factura_data.globals.num_periodes < 3:
                <div class="energy_child_info">
            % else:
                <div>
            %endif
                <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_graphic/energy_consumption_graphic.mako" args="energy=factura_data.energy_consumption_graphic" />
                <%include file="/giscedata_facturacio_comer_som/report/components/meters/meters.mako" args="meters=factura_data.meters,location='down'" />
            </div>
        %endif
    </div>
    <%include file="/giscedata_facturacio_comer_som/report/components/contract_data/contract_data.mako" args="cd=factura_data.contract_data" />
    <%include file="/giscedata_facturacio_comer_som/report/components/emergency_complaints/emergency_complaints.mako" args="ec=factura_data.emergency_complaints,location='up'" />
    <p style="page-break-after:always"></p>
    <%include file="/giscedata_facturacio_comer_som/report/components/amount_destination/amount_destination.mako" args="ad=factura_data.amount_destination" />

    <!-- LECTURES REACTIVA I MAXÍMETRE -->
    <div class="other_measures">
        <%include file="/giscedata_facturacio_comer_som/report/components/reactive_readings_table/reactive_readings_table.mako" args="readings_r=factura_data.reactive_readings_table" />
        <%include file="/giscedata_facturacio_comer_som/report/components/maximeter_readings_table/maximeter_readings_table.mako" args="readings_m=factura_data.maximeter_readings_table" />
    </div>

    <!-- DETALL FACTURA -->
        <div class="invoice_detail">
            <h1>${_(u"DETALL DE LA FACTURA")}</h1>
            % if factura_data.globals.is_6x:
            <div class="row">
                <div class="column">
            %endif
                    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_power/invoice_details_power.mako" args="id_power=factura_data.invoice_details_power" />
                    <hr/>
                    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_energy/invoice_details_energy.mako" args="id_energy=factura_data.invoice_details_energy" />
                    <hr/>
                    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_generation/invoice_details_generation.mako" args="id_generation=factura_data.invoice_details_generation" />
            % if factura_data.globals.is_6x:
                </div>
            </div>
            <%include file="/giscedata_facturacio_comer_som/report/components/hourly_curve/hourly_curve.mako" args="hc=factura_data.hourly_curve" />
            %endif
            <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_reactive/invoice_details_reactive.mako" args="id_reactive=factura_data.invoice_details_reactive" />
            <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_other_concepts/invoice_details_other_concepts.mako" args="id_other=factura_data.invoice_details_other_concepts" />
        </div>
        <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_comments/invoice_details_comments.mako" args="id_comments=factura_data.invoice_details_comments" />
        <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_tec271/invoice_details_tec271.mako" args="id_tec271=factura_data.invoice_details_tec271" />
        <%include file="/giscedata_facturacio_comer_som/report/components/emergency_complaints/emergency_complaints.mako" args="ec=factura_data.emergency_complaints,location='down'" />
    <p style="page-break-after:always"></p>
    <%include file="/giscedata_facturacio_comer_som/report/components/electricity_information/electricity_information.mako" args="elec_info=factura_data.electricity_information" />
    <%include file="/giscedata_facturacio_comer_som/report/components/environmental_impact/environmental_impact.mako" args="ei=factura_data.environmental_impact" />
    <%include file="/giscedata_facturacio_comer_som/report/components/gdo/gdo.mako" args="gdo=factura_data.gdo" />
    <p style="font-size: .8em; float: right">
    ${_(u"Informació sobre protecció de dades: Les dades personals tractades per gestionar la relació contractual i, si s'escau, remetre informació comercial per mitjans electrònics, es conservaran fins a la fi de la relació, baixa comercial o els terminis de retenció legals. Pots exercir els teus drets a l'adreça postal de Som Energia com a responsable o a somenergia@delegado-datos.com .")}<br />
    </p>
% endif
</div>

<script>
var factura_id = ${factura.id}
</script>

</div>
% if comptador_factures+1 < len(objects):
    <p style="page-break-after:always"></p>
% endif
%endfor
</body>
</html>
