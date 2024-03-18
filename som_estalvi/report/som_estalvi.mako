## -*- coding: utf-8 -*-
<%namespace file="som_estalvi/report/components/capcalera.mako" import="capcalera"/>
<%namespace file="som_estalvi/report/components/resum_facturacio_anual.mako" import="resum_facturacio_anual"/>
<%namespace file="som_estalvi/report/components/analisi_potencies.mako" import="analisi_potencies"/>
<%namespace file="som_estalvi/report/components/footer.mako" import="footer"/>
<%namespace file="som_estalvi/report/components/graphic.mako" import="graphic"/>

<!DOCTYPE html>
<html lang="es">
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <head>
        <script src="${addons_path}/som_estalvi/report/assets/d3.v6.js"></script>
        <link rel="stylesheet" href="${addons_path}/som_estalvi/report/som_estalvi.css">
        <style>
            @font-face {
                font-family: "Montserrat-Medium";
                src: url("${assets_path}/fonts/Montserrat/Montserrat-Medium.ttf") format('truetype');
                font-weight: normal;
            }
        </style>
    </head>
    <body>
        %for informe in objects:
            <script>
            </script>
            <div class="a4">
                <div class="page-content">
                    <div class="content">
                        ${capcalera(informe['titular'])}
                        ${resum_facturacio_anual(informe['costs'])}
                        ${analisi_potencies(informe['potencia'])}
                        ${footer()}
                    </div>
                </div>
            </div>
            ${graphic(informe['costs'])}
        %endfor
    </body>
</html>
