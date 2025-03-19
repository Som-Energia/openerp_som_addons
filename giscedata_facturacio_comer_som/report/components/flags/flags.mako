<%page args="flags" />
% if flags.is_autoconsum or flags.is_gkwh:
    <style>
    <%include file="flags.css" />
    </style>
    % if flags.is_autoconsum and flags.is_gkwh:
          <div class="logo_little_left">
              <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/flags/${flags.autoconsum_flag}" width="65px"/>
          </div>
          <div class="logo_little_right">
              <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/flags/${flags.gkwh_flag}" width="65px"/>
          </div>
    % elif flags.is_autoconsum:
          <div class="logo_little_center">
              <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/flags/${flags.autoconsum_flag}" width="65px"/>
          </div>
    % elif flags.is_gkwh:
          <div class="logo_little_center">
              <img src="${addons_path}/giscedata_facturacio_comer_som/report/components/flags/${flags.gkwh_flag}" width="65px"/>
          </div>
    % endif
% endif
