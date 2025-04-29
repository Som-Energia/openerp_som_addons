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
<%namespace file="som_polissa_condicions_generals/report/components/gurb/gurb.mako" import="gurb"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/ccee.mako" import="gurb_ccee_ca"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/ccee.mako" import="gurb_ccee_es"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/baixa.mako" import="gurb_baixa_ca"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/baixa.mako" import="gurb_baixa_es"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/autoritzacio_representant.mako" import="gurb_baixa_autoritzacio_ca"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/autoritzacio_representant.mako" import="gurb_baixa_autoritzacio_es"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/acord_repartiment.mako" import="gurb_acord_ca"/>
<%namespace file="som_polissa_condicions_generals/report/components/gurb/acord_repartiment.mako" import="gurb_acord_es"/>

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
                        %if "gurb" in informe:
                            ${gurb(informe['gurb'])}
                        %endif
                        ${payment_info(informe['polissa'])}
                        ${disclaimers(informe['polissa'])}
                        ${footer(informe['polissa'], informe['titular'])}
                        <p style="page-break-after:always;"></p>
                        %if informe['titular']['lang'] == 'ca_ES':
                            ${generals_ca()}
                            %if informe['prices']['mostra_indexada']:
                                ${indexada_ca()}
                                <p style="page-break-after:always;"></p>
                            %endif
                            %if "gurb" in informe:
                                ${gurb_ccee_ca()}
                                ${gurb_acord_ca()}
                                ${gurb_baixa_autoritzacio_ca(informe['gurb'])}
                                ${gurb_baixa_ca(informe['gurb'])}
                            %endif
                        %else:
                            ${generals_es()}
                            %if informe['prices']['mostra_indexada']:
                                ${indexada_es()}
                                <p style="page-break-after:always;"></p>
                            %endif
                            %if "gurb" in informe:
                                ${gurb_ccee_es()}
                                ${gurb_acord_es()}
                                ${gurb_baixa_autoritzacio_es(informe['gurb'])}
                                ${gurb_baixa_es(informe['gurb'])}
                            %endif
                        %endif
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>
