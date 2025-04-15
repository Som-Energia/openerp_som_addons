<%page args="id" />
<style>
<%include file="energy_consumption_detail_td.css" />
</style>
% for meter in id.meters:
    <div class="energy_consumption_detail_td_block">
        <h1>${_(u"Número de comptador: %s") %(meter.name)}</h1>
        <table id="energy_consumption_detail_td">
            <tr>
                <th class="concepte_td">${_(u"Tipus")}</th>
                <th class="detall_td">${_(u"Detall de lectures")}</th>
                % if len(meter.showing_periods) == 3:
                    <th class="periods_td">${_(u"Punta")}</th>
                    <th class="periods_td">${_(u"Pla")}</th>
                    <th class="periods_td">${_(u"Vall")}</th>
                % else:
                    % for period in meter.showing_periods:
                        <th class="periods_td">${_(u"%s") %(period)}</th>
                    % endfor
                % endif
                <th class="info_td"></th>
            </tr>
            <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td_base/energy_consumption_detail_td_base.mako" args="meter=meter.active" />
            <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td_surplus/energy_consumption_detail_td_surplus.mako" args="meter=meter.surplus" />
            <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td_base/energy_consumption_detail_td_base.mako" args="meter=meter.inductive" />
            <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td_base/energy_consumption_detail_td_base.mako" args="meter=meter.capacitive" />
            % if meter == id.meters[-1]:
                <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td_maximetre/energy_consumption_detail_td_maximetre.mako" args="meter=meter.maximeter" />
            % endif
        </table>
    </div>
%  endfor
%for coll in id.collectives:
    <div class="energy_consumption_detail_td_block">
        <h1>${_(u"Autoconsum col·lectiu: %s") %(coll.name)}</h1>
        <table id="energy_consumption_detail_td">
            <tr>
                <th class="concepte_td">${_(u"Tipus")}</th>
                <th class="detall_td">${_(u"Detall de lectures")}</th>
                % if len(coll.showing_periods) == 3:
                    <th class="periods_td">${_(u"Punta")}</th>
                    <th class="periods_td">${_(u"Pla")}</th>
                    <th class="periods_td">${_(u"Vall")}</th>
                % else:
                    % for period in coll.showing_periods:
                        <th class="periods_td">${_(u"%s") %(period)}</th>
                    % endfor
                % endif
                <th class="info_td"></th>
            </tr>
            <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td_collective/energy_consumption_detail_td_collective.mako" args="coll=coll.generated" />
        </table>
    </div>
% endfor
<div class="energy_consumption_detail_td_block">
    <%include file="/giscedata_facturacio_comer_som/report/components/energy_consumption_detail_td_info/energy_consumption_detail_td_info.mako" args="id_info=id.info" />
</div>
