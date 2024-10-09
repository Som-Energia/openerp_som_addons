<%page args="id" />
<style>
<%include file="invoice_details_td.css" />
</style>

<table id="invoice_detail_td">
    <tr>
        <th class="concepte_td">${_(u"Concepte")}</th>
        <th class="detall_td">${_(u"Detall")}</th>
        % if len(id.showing_periods) == 3:
            <th class="periods_td">${_(u"Punta")}</th>
            <th class="periods_td">${_(u"Pla")}</th>
            <th class="periods_td">${_(u"Vall")}</th>
        % else:
            % for period in id.showing_periods:
                <th class="periods_td">${_(u"%s") %(period)}</th>
            % endfor
        % endif
        <th class="total_td">${_(u"Total conceptes")}</th>
        % if id.iva_column:
            % if id.is_canaries:
                <th class="iva_td">${_(u"IGIC")}</th>
            % else:
                <th class="iva_td">${_(u"IVA")}</th>
            % endif
        % endif
    </tr>
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_power/invoice_details_td_power.mako" args="id=id.power" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_power_tolls/invoice_details_td_power_tolls.mako" args="id=id.power_tolls" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_power_charges/invoice_details_td_power_charges.mako" args="id=id.power_charges" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_power_discount_BOE17_2021/invoice_details_td_power_discount_BOE17_2021.mako" args="id=id.power_discount_BOE17_2021" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_excess_power_maximeter/invoice_details_td_excess_power_maximeter.mako" args="id=id.excess_power_maximeter" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_excess_power_quarterhours/invoice_details_td_excess_power_quarterhours.mako" args="id=id.excess_power_quarterhours" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_energy/invoice_details_td_energy.mako" args="id=id.energy" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_energy_generationkwh/invoice_details_td_energy_generationkwh.mako" args="id=id.energy" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_energy_tolls/invoice_details_td_energy_tolls.mako" args="id=id.energy_tolls" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_energy_charges/invoice_details_td_energy_charges.mako" args="id=id.energy_charges" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_energy_discount_BOE17_2021/invoice_details_td_energy_discount_BOE17_2021.mako" args="id=id.energy_discount_BOE17_2021" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_bo_social_2023/invoice_details_td_bo_social_2023.mako" args="bs=id.bo_social_2023" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_generation/invoice_details_td_generation.mako" args="id=id.generation" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_inductive/invoice_details_td_inductive.mako" args="id=id.inductive" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_capacitive/invoice_details_td_capacitive.mako" args="id=id.capacitive" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_other_concepts/invoice_details_td_other_concepts.mako" args="id=id.other_concepts" />
    <%include file="/giscedata_facturacio_comer_som/report/components/invoice_details_td_flux_solar/invoice_details_td_flux_solar.mako" args="fs=id.flux_solar" />
    <tr class="total_factura_row">
        <td class="total_factura_text" colspan="${len(id.showing_periods)+2}">${_(u"TOTAL FACTURA")}</td>
        <td class="subtotal">${_(u"%s €") % formatLang(id.amount_total)}</td>
        % if id.iva_column:
            <td></td>
        % endif
    </tr>
</table>
