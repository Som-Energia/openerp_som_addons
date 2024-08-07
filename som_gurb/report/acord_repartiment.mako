## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html lang="es">
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <head>
        <link rel="stylesheet" href="${addons_path}/som_gurb/report/som_gurb.css">
        <title>${_(u"Autorització del representant de l'autoconsum col·lectiu")}</title>
        <style>
            @font-face {
                font-family: "Montserrat-Medium";
                src: url("${assets_path}/fonts/Montserrat/Montserrat-Medium.ttf") format('truetype');
                font-weight: normal;
            }
            body {
                font-size: 9pt;
            }
            table {
                border-collapse: collapse;
                border: 2px solid rgb(140 140 140);
                font-family: sans-serif;
                font-size: 7pt;
                letter-spacing: 1px;
            }

            caption {
                caption-side: bottom;
                padding: 10px;
                font-weight: bold;
            }

            thead,
            tfoot {
                background-color: rgb(228 240 245);
            }

            th,
            td {
                border: 1px solid rgb(160 160 160);
                padding: 8px 10px;
            }

            th {
                text-align: center;
            }

            td:last-of-type {
                text-align: center;
            }

            tbody > tr:nth-of-type(even) {
                background-color: rgb(237 238 242);
            }

            tfoot th {
                text-align: right;
            }

            tfoot td {
                font-weight: bold;
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
                        <h2 style="text-align: center;">${_(u"ACORD DE REPARTIMENT D'ENERGIA EN AUTOCONSUM COL·LECTIU AMB EXCEDENTS I COMPENSACIÓ")}</h1>
                        <p>
                            ${_(u"En aplicació de Reial Decret 244/2019 de 5 d'abril, els següents consumidros vam acordar associar-nos a la instal·lació d'autoconsum col·lectiu d'energia elèctrica amb les següents caractarístiques")}
                        </p>
                        <p>
                            <input type="checkbox" ${informe["compensacio"] and "checked"}> ${_(u"AMB excedents acollida a compensació")}
                        </p>
                        <p>
                            <b> ${_(u"Codi autoconsum (CAU):")} </b> ${informe["productora"]["cau"]}
                        </p>
                        <table>
                            <thead>
                                <tr>
                                    <th colspan="2">
                                        ${_("Productora Associada (titular de la instal·lació de generació)")}
                                    </th>
                                    <th>
                                        ${_("NIF")}
                                    </th>
                                    <th>
                                        ${_("CIL")}
                                    </th>
                                    <th>
                                        ${_("Coefiecient (α)")}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>
                                        1
                                    </td>
                                    <td>
                                        ${informe["productora"]["nom"]}
                                    </td>
                                    <td>
                                        ${informe["productora"]["nif"]}
                                    </td>
                                    <td>
                                        ${informe["productora"]["cil"]}
                                    </td>
                                    <td>
                                        1
                                    </td>
                                </tr>
                            </tbody>
                        </table>

                        <br/>

                        <table>
                            <thead>
                                <tr>
                                    <th colspan="2">
                                        ${_("Consumidor/a Associat/da (titular del subministrament)")}
                                    </th>
                                    <th>
                                        ${_("NIF")}
                                    </th>
                                    <th>
                                        ${_("CUPS")}
                                    </th>
                                    <th>
                                        ${_("Coef. de repartiment (β)")}
                                    </th>
                                </tr>
                            </thead>
                            %for consumidor in informe["consumidors"]:
                                <tbody>
                                    <tr>
                                        <td>
                                            ${consumidor["nombre"]}
                                        </td>
                                        <td>
                                            ${consumidor["nom"]}
                                        </td>
                                        <td>
                                            ${consumidor["nif"]}
                                        </td>
                                        <td>
                                            ${consumidor["cups"]}
                                        </td>
                                        <td>
                                            ${consumidor["coef"]} %
                                        </td>
                                    </tr>
                                </tbody>
                            %endfor
                        </table>

                        <p style="page-break-after:always"></p>
                        <br/> <br/> <br/>

                        ${_(u"Amb la signatura d'aquest acord:")}
                        <ul>
                            <li>
                                ${_(u"Els consumidors ens acollim voluntàriament al mecanisme de compensació simplificada entre els dèficits de consum de cada consumidor i la totalitat dels excedents de la instal·lació d'autoconsum, la generació elèctrica neta serà repartida d'acord amb els coeficients de repartiment (β) indicats, tal com estableix el Reial Decret 244/2019, de 5 d'abril")}
                            </li>
                            <li>
                                ${_(u"Totes les parts ens obliguen a notificar aquest acord de repartiment a la companyia comercialitzadora amb la qual tenim contractat el subministrament elèctric, amb la instrucció de realitzar tots els tràmits necessaris relacionats amb l'activació de l'autoconsum col·lectiu i l'aplicació del present acord de repartiment, en particular el mecanisme de compensació simplificada dels excedents de la instal·lació d'autoconsum a la qual ens associem i l'inici del mecanisme de compensació en el següent període de facturació des de la recepció d'aquest acord en els termes previst al Reial Decret 244/2019 i la normativa que el desenvolupa.")}
                            </li>
                            <li>
                                ${_(u"La Productora Associada es compromet a informar a les Consumidores, directament a través del gestor d'aquest autoconsum col·lectiu (SOM ENERGIA SCCL), de qualsevol inicidència que afecti a la instal·lació")}
                            </li>
                            <li>
                                ${_(u"Totes les parts, tant Productora Associada com Consumidores, s'obliguen a mantenir absoluta confidencialitat sobre les dades personals al fet que tingui accés amb motiu de la signatura d'aquest Acord de Repartiment.")}
                            </li>
                            <li>
                                ${_(u"Totes les parts, tant Productora Associada com Consumidores, accepten expressament la cessió de les dades personals recollides en aquest document a la resta de participants, a les seves respectives comercialitzadores, a la distribuïdora propietaria de la xarxa a la que es conecten, a les autoritats competents, a la empresa instaladora o mantenedora de la instal·lació associada, amb la sola finalitat de gestionar i tramitar l'aplicació del present acord de repartiment i del autoconsum col·lectiu al que fa referència.")}
                            </li>
                            <li>
                                ${_(u"Totes les parts queden informades que el responsable del tractament de les dades personals objecte de la cessió és Som Energia SCCL, en tant que actua com a representant de l'autoconsum col·lectiu, amb la finalitat de gestionar i tramitar l'aplicació del present acord de repartiment i del autoconsum col·lectiu al que fa referència. Per tant, tret l'obligada cessió indicada, les dades no seran cedides excepte en els supòsits legalment exigits i només es conservaran mentre el titular de les dades estigui associat al autoconsum col·lectiu i, un cop finalitzada aquesta pertinença, dins dels terminis legals previstos. Pots retirar el teu consentiment en qualsevol moment i exercir el teu dret d'accés, rectificació, supressió, portabilitat, limitació i oposició dirigint-te a somenergia@delegado-datos.com (delegat de protecció de dades). En cas de divergèncias, pots presentar una reclamació davant l'Agència de Protecció de Dades (www.aepd.es)")}
                            </li>
                        </ul>
                        <p>A Girona, ${informe['day']} ${informe['month']} ${informe['year']}</p>
                        <p>${_(u"Les CONSUMIDORES associades:")}</p>
                        <p>${_(u"Som Energia SCCL")}</p>
                        <br/>
                        <br/>
                        <br/>
                        <br/>
                        <br/>
                        <p>${_(u"F55091367")}</p>
                        <p>${_(u"La PRODUCTORA associada:")}</p>
                        <p>${informe["productora"]["nom"]}</p>
                        <br/>
                        <br/>
                        <br/>
                        <br/>
                        <br/>
                        <p>${informe["productora"]["nif"]}</p>
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>
