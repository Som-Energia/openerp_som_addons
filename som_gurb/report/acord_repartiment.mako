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
            /* Create three equal columns that floats next to each other */
            .column {
              float: left;
              width: 30%;
              padding: 10px;
            }

            /* Clear floats after the columns */
            .row:after {
              content: "";
              display: table;
              clear: both;
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
                            ${_(u"En aplicació del Reial decret 244/2019, de 5 d'abril, els consumidors següents vam acordar associar-nos a la instal·lació d'autoconsum col·lectiu d'energia elèctrica amb les característiques següents: ")}
                        </p>
                        <p>
                            <input type="checkbox" ${informe["compensacio"] and "checked"}> ${_(u"AMB excedents acollits a compensació simplificada")}</input>
                        </p>
                        <p>
                            <input type="checkbox" ${not informe["compensacio"] and "checked"}> ${_(u"AMB excedents no acollits a compensació simplificada")}</input>
                        </p>
                        <p>
                            <b> ${_(u"Codi autoconsum (CAU):")} </b> ${informe["productora"]["cau"]}
                        </p>
                        <table>
                            <thead>
                                <tr>
                                    <th colspan="2">
                                        ${_("<b>Productora Associada</b> (titular de la instal·lació de generació)")}
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
                                        ${_("<b>Consumidora Associada</b> (titular del subministrament)")}
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
                                ${_(u"Les persones consumidores ens acollim voluntàriament al mecanisme de compensació simplificada entre els dèficits de consum de cada una i la totalitat dels excedents de la instal·lació d'autoconsum. La generació elèctrica neta es repartirà d'acord amb els coeficients de repartiment (β) indicats, tal com estableix el Reial decret 244/2019, de 5 d'abril. ")}
                            </li>
                            <li>
                                ${_(u"Les persones consumidores manifesten que SOM ENERGIA, SCCL, actua com a gestora i titular dels drets d'explotació propis de la Instal·lació, legalitzats en règim d'autoconsum col·lectiu amb excedents. Especialment en el cas d'estar acollides a la modalitat d'autoconsum amb excedents sense compensació simplificada, les Parts assumeixen i entenen que l’energia produïda per la Instal·lació que, per falta de consum a horari suficient del CUPS associat no pot ser considerada energia horària autoconsumida, correspon en exclusiva a la titular de la Instal·lació, tant la seva propietat com la seva valoració, formes d'aprofitament i en general qualsevol altre aspecte relatiu a aquesta energia.")}
                            </li>
                            <li>
                                ${_(u"Totes les parts ens obliguem a notificar aquest acord de repartiment a la companyia comercialitzadora amb la qual tenim contractat el subministrament elèctric, amb la instrucció de dur a terme tots els tràmits necessaris relacionats amb l’activació de l’autoconsum col·lectiu i l’aplicació del present acord de repartiment, en particular el mecanisme de compensació simplificada dels excedents de la instal·lació d'autoconsum a la qual ens associem i l'inici del mecanisme de compensació en el següent període de facturació des de la recepció d'aquest acord en els termes previstos al Reial decret 244/2019 i la normativa que el desenvolupa. ")}
                            </li>
                            <li>
                                ${_(u"La productora associada es compromet a informar les consumidores, directament o a través del gestor d’aquest autoconsum col·lectiu (SOM ENERGIA, SCCL), de qualsevol incidència que afecti la instal·lació.")}
                            </li>
                            <li>
                                ${_(u"Totes les parts, tant la productora associada com consumidores, s'obliguen a mantenir absoluta confidencialitat sobre les dades personals a les quals tenen accés amb motiu de la signatura d'aquest acord de repartiment.")}
                            </li>
                            <li>
                                ${_(u"Totes les parts, tant la productora associada com consumidores, accepten expressament la cessió de les dades personals recollides en aquest document a la resta de participants, a les seves respectives comercialitzadores, a la distribuïdora propietària de la xarxa a la qual es connecten, a les autoritats competents, a l'empresa instal·ladora o mantenidora de la instal·lació associada i a Som Energia, SCCL, en tant que gestora de la instal·lació associada, i amb la sola finalitat de gestionar i tramitar l’aplicació del present acord de repartiment i de l'autoconsum col·lectiu al qual fa referència.")}
                            </li>
                            <li>
                                ${_(u"Totes les parts queden informades que el responsable del tractament de les dades personals objecte de la cessió és Som Energia, SCCL, en tant que actua com a representant de l’autoconsum col·lectiu, amb la finalitat de gestionar i tramitar l’aplicació del present acord de repartiment i de l'autoconsum col·lectiu al qual fa referència. Per tant, tret de l'obligada cessió indicada, les dades no seran cedides, excepte en els supòsits legalment exigits, i només es conservaran mentre el titular de les dades estigui associat a l'autoconsum col·lectiu i, un cop finalitzada aquesta pertinença, dins dels terminis legals previstos. Es pot retirar el consentiment en qualsevol moment i exercir el dret d'accés, rectificació, supressió, portabilitat, limitació i oposició dirigint-se a somenergia@delegado-datos.com (delegat de protecció de dades). En cas de divergències, es pot presentar una reclamació davant l'Agència de Protecció de Dades (www.aepd.es).")}
                            </li>
                        </ul>
                        <p style="page-break-after:always"></p>
                        <p>A Girona, ${informe['day']} de ${informe['month']} de ${informe['year']}</p>
                        <p>${_(u"Les CONSUMIDORES associades:")}</p>
                        <% i = 0 %>
                        %for consumidor in informe["consumidors"]:
                            %if i % 3 == 0:
                                <div class="row">
                            %endif
                            <div class="column">
                                <p>${consumidor["nom"]}</p>
                                <br/>
                                <br/>
                                <p>${consumidor["nif"]}</p>
                            </div>
                            <% i += 1 %>
                            %if i % 3 == 0:
                                </div>
                            %endif
                            %if i % 21 == 0:
                                <p style="page-break-after:always"></p>
                            %endif
                        %endfor
                        %if not (i % 3 == 0):
                            </div>
                        %endif
                        <p>${_(u"La PRODUCTORA associada:")}</p>
                        <p>${informe["productora"]["nom"]}</p>
                        <br/>
                        <br/>
                        <p>${informe["productora"]["nif"]}</p>
                    </div>
                </div>
            </div>
        %endfor
    </body>
</html>
