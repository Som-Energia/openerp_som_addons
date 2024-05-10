## -*- coding: utf-8 -*-
<%namespace file="som_polissa_condicions_generals/report/components/capcalera.mako" import="capcalera"/>

<!DOCTYPE html>
<html lang="es">
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <head>
        <link rel="stylesheet" href="${addons_path}/som_assets/css/report_base_style.css">
        <link rel="stylesheet" href="${addons_path}/som_polissa_condicions_generals/report/condicions_particulars_puppeteer.css">
        <title>${_(u"SomEnergia Condicions Particulars")}</title>
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
                        ${capcalera(informe['polissa'])}
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>