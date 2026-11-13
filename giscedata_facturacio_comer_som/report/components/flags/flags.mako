<%page args="flags" />
<%
from giscedata_facturacio_comer_som.giscedata_facturacio_report import get_invoice_flag_images
images = flags.get('flag_images')
if images is None:
    images = get_invoice_flag_images(flags)
%>
% if images:
    <style>
    <%include file="flags.css" />
    </style>
    <div class="invoice_flags">
    % for image in images:
        <img src="${image['src'] if image['src'].startswith('data:') else addons_path + image['src']}" width="65px"/>
    % endfor
    </div>
% endif
