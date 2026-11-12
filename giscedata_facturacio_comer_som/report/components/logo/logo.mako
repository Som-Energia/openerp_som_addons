<%page args="logo" />
<%import base64 %>
<div class="logo" style="margin-bottom: 15px; ">
    % if logo.has_agreement_partner:
        <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/logo/${logo.logo}" width="95px"/>
        <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/logo/${logo.logo_agreement_partner}" width="95px"/>
    % else:
        % if logo.has_auvi:
            <%auvi_logo_base64 = base64.b64encode(logo.auvi_logo).decode("utf-8") %>
            <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/logo/${logo.logo}" width="95px"/>
            <img src="data:image/png;base64,${auvi_logo_base64}" width="95px" />
        % else:
            <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/logo/${logo.logo}" width="125px"/>
        % endif
    % endif
</div>
