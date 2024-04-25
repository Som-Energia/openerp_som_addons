## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html lang="es">
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <head>
        <link rel="stylesheet" href="${addons_path}/som_gurb/reports/som_gurb.css">
        <title>${_(u"CCEE GURB")}</title>
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
                        <h2 style="text-align: center;">Annex III</h1>
                        <h2 style="text-align: center;">Autorització del representant de l’autoconsum col·lectiu</h1>
                        <p>(Nom i cognoms) _____, major d'edat, amb domicili a __________ i DNI número _________, de forma lliure i voluntària i en ple ús de les meves facultats, i en tant que titular del CUPS _______________. </p>
                        <p>CONFIRMO que tant en el cas de la resolució del Contracte de Subministrament amb SOM ENERGIA, SCCL, com en el cas de la meva baixa del GURB, segons preveuen les seves Condicions Específiques, deixaré de formar part de l’autoconsum col·lectiu CAU que se m’hagi assignat per part de la distribuïdora i notificat per part de SOM ENERGIA, SCCL, a través de correu electrònic; per tant, autoritzo SOM ENERGIA SCCL, com a representant d’aquest autoconsum col·lectiu, i en particular Nuria Palmada García o qualsevol altra persona apoderada de SOM ENERGIA, SCCL, a fer tots els tràmits necessaris per gestionar-ne la modificació.</p>
                        <p> __________________________, ______ de _____________________de 20 _______</p>
                        <p>L'Autoritzant</p>
                        <p>[NOM/RAÓ SOCIAL] [DNI/CIF]</p>
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>
