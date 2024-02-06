<%page args="logo" />
<div class="logo" style="margin-bottom: 15px; ">
    % if logo.has_agreement_partner:
        <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/logo/${logo.logo}" width="95px"/>
        <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/logo/${logo.logo_agreement_partner}" width="95px"/>
    % else:
        <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/logo/${logo.logo}" width="125px"/>
    % endif
</div>
