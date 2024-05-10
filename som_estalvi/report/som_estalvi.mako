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
        <script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.common.min.js" integrity="sha512-klHlINboj5r1sfTjdyb2PJn7ixcYb5zN+WC/gbFlK3r8/nmhmwQ3yvi5q49tX39DcHX/HwPnXTIblG5/cb6IEA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        <link rel="stylesheet" href="${addons_path}/som_estalvi/report/som_estalvi.css">
        <title>${_(u"SomEnergia informe anual")}</title>
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
