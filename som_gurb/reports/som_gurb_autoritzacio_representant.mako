## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html lang="es">
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <head>
        <link rel="stylesheet" href="${addons_path}/som_gurb/reports/som_gurb.css">
        <title>${_(u"Autorització del representant de l’autoconsum col·lectiu")}</title>
        <style>
            @font-face {
                font-family: "Montserrat-Medium";
                src: url("${assets_path}/fonts/Montserrat/Montserrat-Medium.ttf") format('truetype');
                font-weight: normal;
            }
            body {
                font-size: 9pt;
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
                        <h2 style="text-align: center;">${_(u"Autorització del representant de l’autoconsum col·lectiu")}</h1>
                        <p>
                            ${_(u"Atès el que preveu la normativa sectorial aplicable i en particular els articles 9 i 44 de la Llei 24/2013; els articles 3, 4, 16 bis de l’Annex I del RD 244/2019; i la disposició transitòria segona de l'Ordre TED /1247/2021, així com els principis generals, en particular el de llibertat de forma, i els articles 1710 i 1280 del Codi Civil Espanyol.")}
                        </p>
                        %if informe['is_enterprise']:
                            <p>
                                ${informe["representative"]["name"]}, ${_(u"major d'edat, amb NIF número")} ${informe["representative"]['vat']} ${_(u"i domicili a")} ${informe["representative"]["address"]}, ${_(u"actuant en la meva condició de")} ${_(u"REPRESENTANT")}, ${_(u"i manifestant que en aquesta condició disposo de les facultats suficients, actuant EN NOM I REPRESENTACIÓ DE")} ${informe["name"]} , ${_(u"amb NIF")} ${informe['nif']} ${_(u"i domicili social a")} ${informe['address']} ${_(u"com a titular del CUPS")} ${informe['cups']}${_(u"(“Autoritzant”)")}
                            </p>
                        %else:
                            <p>
                                ${informe['name']},  ${_(u"major d'edat, amb domicili a")} ${informe['address']} ${_(u"i DNI número")} ${informe['nif']}, ${_(u"de forma lliure i voluntària i en ple ús de les meves facultats, i en tant que titular del CUPS")} ${informe['cups']} ${_(u"associat a l'autoconsum col·lectiu CAU")} ${informe["cau"]} ${_(u"(“Autoritzant”)")}
                            </p>
                        %endif
                        <p>
                            <b> ${_(u"AUTORITZO:")} </b>
                        </p>
                        <p>
                            ${_(u"SOM ENERGIA, SCCL, amb NIF F55091367 i domicili social al carrer  Pic de Peguera 11, planta, 17003 Girona (“Autoritzada”) a actuar com a representant  integral del meu CUPS en tant que associat a l'autoconsum col·lectiu CAU provisional")} ${informe["cau"]}, ${_(u"per termini il·limitat, a fi que pugui dur a terme les ACTUACIONS següents:")}
                        </p>
                        <ul>
                            <li>
                                ${_(u"Signar en nom meu l’acord de repartiment que reculli els coeficients de repartiment pels quals s'assignen coeficients de repartiment a CUPS de la meva titularitat, així com qualsevol modificació d'aquests acords.")}
                            </li>
                            <li>
                                ${_(u"Comunicar directament en nom meu aquest acord de repartiment (i les seves modificacions), així com el fitxer de coeficients de repartiment corresponent a l'empresa distribuïdora propietària de la xarxa a la qual em connecto, així com a l'empresa comercialitzadora amb què tingui en cada moment contractat el subministrament elèctric.")}
                            </li>
                            <li>
                                ${_(u"Fer en nom meu qualsevol gestió o comunicació amb la distribuïdora que sigui necessària, convenient, accessòria o relacionada amb l'aplicació del terme de descompte per retard en activació d'autoconsum (art. 16.bis Reial decret 244/2019).")}
                            </li>
                            <li>
                                ${_(u"Recepcionar i ventilar en nom meu, per qualsevol via, qualsevol comunicació necessària, convenient, accessòria o relacionada amb les actuacions indicades més amunt, incloent-hi aquelles per les quals es tractin o comparteixin els acords de repartiment o les seves modificacions, sigui amb la distribuïdora, l'Autoritzada o altres signants, presents o futurs.")}
                            </li>
                            <li>
                                ${_(u"Cedir les meves dades personals recollides en aquest document a la resta de participants en l'autoconsum col·lectiu CAU provisional")} ${informe["cau"]}, ${_(u"a les seves respectives comercialitzadores, a la distribuïdora propietària de la xarxa a la qual es connectin, a les autoritats competents, a l'empresa instal·ladora o mantenidora de la instal·lació associada, amb la sola finalitat de gestionar i tramitar l'aplicació de l'acord de repartiment i l'activació, modificació o baixa de l'autoconsum col·lectiu al qual fa referència.")}
                            </li>
                        </ul>
                        <p>
                            ${_(u"Llevat l'obligada cessió indicada, declaro que conec que Som Energia, SCCL, és la responsable del tractament de les dades personals objecte d'aquesta autorització, que m'ha informat clarament que les dades no seran cedides, excepte en els supòsits legalment exigits, que només es conservaran mentre la present autorització estigui vigent i, una vegada finalitzada aquesta, dins dels terminis legals previstos. Així mateix, declaro que Som Energia, SCCL, m'ha informat que puc retirar el meu consentiment en qualsevol moment i exercir el meu dret d'accés, rectificació, supressió, portabilitat, limitació i oposició dirigint-me a somenergia@delegado-datos.com (delegat de protecció de dades). En cas de divergències, puc presentar una reclamació davant l'Agència de Protecció de Dades (www.aepd.es).")}
                        </p>
                        <ul>
                            <li>
                                ${_(u"A dur a terme qualsevol altra actuació que, segons el parer de l'Autoritzada, sigui necessària, convenient, accessòria o relacionada amb les actuacions indicades més amunt.")}
                            </li>
                        </ul>
                        <p> Girona, ${informe['day']} ${informe['month']} ${informe['year']}</p>
                        <p>${_(u"L'Autoritzant")}</p>
                        <p>${informe['name']} ${informe['nif']}</p>
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>
