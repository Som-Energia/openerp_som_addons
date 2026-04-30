# -*- coding: utf-8 -*-
<%namespace file="/giscedata_facturacio/report/resum_factures_emeses/components/taula_factures.mako" import="taula_factures"/>
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

<%def name="capcalera(idx, object)">
    <div class="capcalera">
        <div class="titol-img">
            <div class="titol">${_(u"EXTRACTE DE FACTURES PENDENTS")}</div>
            <img class="company-logo"
                 src="data:image/jpeg;base64,${object['companyia']['logo']}"
                 alt="Empresa"/>
        </div>
        <div class="dades-polissa">
            <div class="linia-compartida">
                <div>
                    <div class="title">${_(u"Titular")}</div>
                    <div class="data">${object['modcons'][idx]['titular']}</div>
                </div>
                <div>
                    <div class="title">${_(u"Pagador")}</div>
                    <div class="data">${object['modcons'][idx]['pagador']}</div>
                </div>
            </div>
            <div class="linia-compartida">
                <div>
                    <div class="title">${_(u"CUPS")}</div>
                    <div class="data">${object['cups']}</div>
                </div>
                <div>
                    <div class="title">${_(u"Contracte")}</div>
                    <div class="data">${object['num_contracte']}</div>
                </div>
                <div>
                    <div class="title">${_(u"Data")}</div>
                    <div class="data">${object['avui']}</div>
                </div>
            </div>
            <div>
                <div>
                    <div class="title">${_(u"Adreça Subministrament")}</div>
                    <div class="data">${object['adreca_subministrament']}</div>
                </div>
            </div>
        </div>
    </div>
</%def>

<%def name="preu_final(idx, imports)">
    <div class="container-preu-final">
        <table class="preu-final">
            <tr>
                <td>${_(u"Subtotal")}</td>
                <td>${imports['total']} €</td>
            </tr>
            <tr>
                <td>${_(u"Pagat")}</td>
                <td>${imports['cobrat']} €</td>
            </tr>
            <tr class="total">
                <td>${_(u"Total")}</td>
                <td>${imports['pendent']} €</td>
            </tr>
        </table>
    </div>
</%def>

</html>
