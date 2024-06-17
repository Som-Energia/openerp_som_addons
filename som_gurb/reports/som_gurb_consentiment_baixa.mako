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
                        <br />
                        <br />
                        <h2 style="text-align: center;">
                        ${_(u"Annex III")}
                        </h1>
                        <br />
                        <h2 style="text-align: center;">
                        ${_(u"Confirmació de baixa en autoconsum col·lectiu")}
                        </h1>
                        <br />
                        % if not data["is_enterprise"]:
                        <p>
                        ${informe['name']}, ${_(u"major d'edat, amb domicili a")} ${informe['address']} ${_(u"i DNI número")} ${informe['nif']}, ${_(u"de forma lliure i voluntària i en ple ús de les meves facultats, i en tant que titular del CUPS")} ${informe['cups']}.
                        </p>
                        % else:
                        <p>
                        ${informe["representative"]["name"]}, ${_(u"major d'edat, amb NIF número")} ${informe["representative"]["vat"]} ${_(u"i domicili a")} ${informe["representative"]["address"]}, ${_(u"actuant en la meva condició de")} ________________, ${_(u"i manifestant que en aquesta condició disposo de les facultats suficients, actuant EN NOM I REPRESENTACIÓ DE")} ${informe["name"]} , ${_(u"amb NIF")} ${informe['nif']} ${_(u"i domicili social a")} ${informe['address']} ${_(u"com a titular del CUPS")} ${informe['cups']}.
                        </p>
                        % endif
                        <p>
                        ${_(u"CONFIRMO que tant en el cas de la resolució del Contracte de Subministrament amb SOM ENERGIA, SCCL, com en el cas de la meva baixa del GURB, segons preveuen les seves Condicions Específiques, deixaré de formar part de l’autoconsum col·lectiu CAU que se m’hagi assignat per part de la distribuïdora i notificat per part de SOM ENERGIA, SCCL, a través de correu electrònic; per tant, autoritzo SOM ENERGIA, SCCL, com a representant d’aquest autoconsum col·lectiu, i en particular Núria Palmada García o qualsevol altra persona apoderada de SOM ENERGIA, SCCL, a fer tots els tràmits necessaris per gestionar-ne la modificació.")}
                        </p>
                        <br />
                        <p>
                        ${_(u"Girona")}, ${informe['day']} ${informe['month']} de ${informe['year']}
                        </p>
                        <br />
                        <p>
                        ${_(u"L'Autoritzant")}
                        </p>
                        <br />
                        <br />
                        <p>
                        ${informe['name']} ${informe['nif']}
                        </p>
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>
