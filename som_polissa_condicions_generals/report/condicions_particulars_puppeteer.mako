## -*- coding: utf-8 -*-
<%namespace file="som_polissa_condicions_generals/report/components/capcalera.mako" import="capcalera"/>
<%namespace file="som_polissa_condicions_generals/report/components/contact_info.mako" import="contact_info"/>
<%namespace file="som_polissa_condicions_generals/report/components/potencies_info.mako" import="potencies_info"/>
<%namespace file="som_polissa_condicions_generals/report/components/prices_info.mako" import="prices_info"/>
<%namespace file="som_polissa_condicions_generals/report/components/payment_info.mako" import="payment_info"/>
<%namespace file="som_polissa_condicions_generals/report/components/disclaimers.mako" import="disclaimers"/>
<%namespace file="som_polissa_condicions_generals/report/components/footer.mako" import="footer"/>
<%namespace file="som_polissa_condicions_generals/report/condicions_generals.mako" import="generals_ca"/>
<%namespace file="som_polissa_condicions_generals/report/condiciones_generales.mako" import="generals_es"/>
<%namespace file="som_polissa_condicions_generals/report/condicions_especifiques_indexada.mako" import="indexada_ca"/>
<%namespace file="som_polissa_condicions_generals/report/condiciones_especificas_indexada.mako" import="indexada_es"/>

<!DOCTYPE html>
<html lang="es">
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <head>
        <style>
            @font-face {
                font-family: "Roboto";
                src: url("${assets_path}/fonts/Roboto/Roboto-Regular.ttf") format('truetype');
                font-weight: normal;
            }
            @font-face {
                font-family: "Roboto";
                src: url("${assets_path}/fonts/Roboto/Roboto-Bold.ttf") format('truetype');
                font-weight: bold;
            }
            @font-face {
                font-family: "Roboto";
                src: url("${assets_path}/fonts/Roboto/Roboto-Thin.ttf") format('truetype');
                font-weight: 200;
            }
        </style>
        <link rel="stylesheet" href="${addons_path}/som_polissa_condicions_generals/report/condicions_particulars_puppeteer.css"/>
    </head>
    <body>
        %for informe in objects:
            <script>
            </script>
            <div class="a4">
                <div class="page-content">
                    <div class="content">
                        ${capcalera(informe['polissa'])}
                        ${contact_info(informe['titular'], informe['cups'])}
                        ${potencies_info(informe['polissa'], informe['potencies'])}
                        ${prices_info(informe['polissa'], informe['prices'])}
                        ${payment_info(informe['polissa'])}
                        ${disclaimers(informe['polissa'])}
                        ${footer(informe['polissa'], informe['titular'])}
                        <p style="page-break-after:always;"></p>
                        %if informe['titular']['lang'] == 'ca_ES':
                            %if informe['prices']['mostra_indexada']:
                                ${indexada_ca()}
                                <p style="page-break-after:always;"></p>
                            %endif
                            ${generals_ca()}
                        %else:
                            %if informe['prices']['mostra_indexada']:
                                ${indexada_es()}
                                <p style="page-break-after:always;"></p>
                            %endif
                            ${generals_es()}
                        %endif
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>
