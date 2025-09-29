# -*- coding: utf-8 -*-
<%namespace file="/giscedata_facturacio/report/resum_factures_deute.mako" import="capcalera, taula_factures, preu_final"/>
<!DOCTYPE html>
<html>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <head>
        <link rel="stylesheet"
              href="${addons_path}/giscedata_facturacio/report/resum_factures_deute.css"/>
        <link rel="stylesheet"
              href="${addons_path}/giscedata_facturacio_som/report/resum_factures_deute.css"/>
    </head>
    <body>
        %for object in objects:
            %for idx, modcon in enumerate(object['modcons']):
                %if object['num_factures'] or not object['num_factures'] and idx == 0:
                    %if idx == 0 :
                        <div class="a4">
                            <div class="page-content first-page">
                                <div class="content">
                                    ${capcalera(idx, object)}
                                    ${taula_factures(idx, modcon['factures']['metadata'], modcon['factures']['data'], modcon['imports'], display_total=False)}
                                    ${preu_final(idx, modcon['imports'])}
                                </div>
                            </div>
                        </div>
                    %endif
                %endif
            %endfor
        %endfor
    </body>
</html>
