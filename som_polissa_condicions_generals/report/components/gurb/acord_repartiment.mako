<%def name="gurb_acord_ca()">
    <p style="page-break-after:always;"></p>
    <br>
    <br>
    <div id="titol">
        <h2 style="font-size: 14px;">Annex I</h2>
    </div>
    <div id="titol">
        <h2 style="text-align: center;">${_(u"ACORD DE REPARTIMENT D'ENERGIA EN AUTOCONSUM COL·LECTIU AMB EXCEDENTS I COMPENSACIÓ")}</h1>
    </div>
    <p>
        ${_(u"En aplicació del Reial decret 244/2019, de 5 d'abril, els consumidors següents acordem associar-nos en una instal·lació d'autoconsum col·lectiu d'energia elèctrica amb les característiques següents:")}
    </p>
    <p>
        <input type="checkbox"> ${_(u"AMB excedents acollits a compensació simplificada")}</input>
    </p>
    <p>
        <input type="checkbox"> ${_(u"AMB excedents no acollits a compensació simplificada")}</input>
    </p>
    <p>
        <b> ${_(u"Codi d'autoconsum (CAU):")} </b>
    </p>
    <p>
        ${_(u"(completar per cada consumidora associada)")}
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
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
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
        <tbody>
            <tr>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
            </tr>
        </tbody>
    </table>

    <p style="page-break-after:always"></p>
    <br/> <br/> <br/>

    ${_(u"Amb la signatura d'aquest acord:")}
    <ul>
        <li>
            ${_(u"En el cas que la instal·lació estigui donada d'alta en la modalitat amb excedents acollida a compensació, les persones consumidores ens acollim voluntàriament al mecanisme de compensació simplificada entre els dèficits de consum de cadascuna i la totalitat dels excedents de la instal·lació d'autoconsum, la generació elèctrica neta es repartirà d'acord amb els coeficients de repartiment (β) indicats, tal com estableix el Reial decret 244/2019, de 5 d'abril.")}
        </li>
        <li>
            ${_(u"Les persones consumidores manifesten que SOM ENERGIA, SCCL, actua com a gestora i titular dels drets d'explotació propis de la Instal·lació, legalitzats en règim d'autoconsum col·lectiu amb excedents. Especialment en el cas d'estar acollides a la modalitat d'autoconsum amb excedents sense compensació simplificada, les Parts assumeixen i entenen que l'energia produïda per la Instal·lació que, per falta de consum horari suficient del CUPS associat no es pot considerar energia horària autoconsumida, correspon en exclusiva a la titular de la Instal·lació, tant la seva propietat com la seva valoració, formes d'aprofitament i, en general, qualsevol altre aspecte relatiu a aquesta energia.")}
        </li>
        <li>
            ${_(u"Totes les parts ens obliguem a notificar aquest acord de repartiment a la companyia comercialitzadora amb la qual tenim contractat el subministrament elèctric, amb la instrucció de fer tots els tràmits necessaris per modificar el Contracte Tècnic d'Accés a xarxes subscrit amb la propietària de la xarxa, a fi d'activar l'autoconsum col·lectiu i aplicar del present acord de repartiment, en particular el mecanisme de compensació simplificada dels excedents de la instal·lació d'autoconsum a la qual ens associem i l'inici del mecanisme de compensació en el següent període de facturació des de la recepció d'aquest acord, en els termes previstos en el Reial decret 244/2019 i la normativa que el desenvolupa.")}
        </li>
        <li>
            ${_(u"La productora associada es compromet a informar les consumidores, directament o a través de la gestora d'aquest autoconsum col·lectiu (SOM ENERGIA, SCCL), de qualsevol incidència que afecti la instal·lació.")}
        </li>
        <li>
            ${_(u"Totes les Parts, tant la Productora Associada com les Consumidores, s'obliguen a mantenir absoluta confidencialitat sobre les dades personals a les quals tenen accés amb motiu de la signatura d'aquest acord de repartiment.")}
        </li>
        <li>
            ${_(u"Totes les parts, tant la Productora Associada com les Consumidores, accepten expressament la cessió de les dades personals recollides en aquest document a la resta de participants, a les seves respectives comercialitzadores, a la distribuïdora propietària de la xarxa a la qual es connecten, a les autoritats competents, a l'empresa instal·ladora o mantenidora de la instal·lació associada i a SOM ENERGIA, SCCL, com a gestora de la instal·lació associada, amb la sola finalitat de gestionar i tramitar l'aplicació d'aquest acord de repartiment i de l'autoconsum col·lectiu a què es refereix.")}
        </li>
        <li>
            ${_(u"Totes les parts queden informades que el responsable del tractament de les dades personals objecte de la cessió és SOM ENERGIA, SCCL, ja que actua com a representant de l'autoconsum col·lectiu, amb la finalitat de gestionar i tramitar l'aplicació d'aquest acord de repartiment i de l'autoconsum col·lectiu al qual fa referència. Per tant, excepte l'obligada cessió indicada, les dades no seran cedides, tret dels supòsits legalment exigits, i només es conservaran mentre el titular de les dades estigui associat a l'autoconsum col·lectiu i, una vegada finalitzada aquesta pertinença, dins dels terminis legals previstos.")}
        </li>
        <li>
            ${_(u"Es pot retirar el consentiment en qualsevol moment i exercir el dret d'accés, rectificació, supressió, portabilitat, limitació i oposició adreçant-se a somenergia@delegado-datos.com (delegat de protecció de dades). En cas de divergències, es pot presentar una reclamació davant l'Agència de Protecció de Dades (www.aepd.es).")}
        </li>
    </ul>
    <p style="page-break-after:always"></p>
    <p>A Girona, ... de ... de ...</p>
    <p>${_(u"Les CONSUMIDORES associades representades pel seu representant, SOM ENERGIA, SCCL, amb NIF F55091367")}</p>
    <p>&nbsp;</p>
    <br/>
    <br/>
    <p>&nbsp;</p>
</%def>

<%def name="gurb_acord_es()">
    <p style="page-break-after:always;"></p>
    <br>
    <br>
    <div id="titol">
        <h2 style="font-size: 14px;">Anexo I</h2>
    </div>
    <div id="titol">
        <h2 style="text-align: center;">${_(u"ACUERDO DE REPARTO DE ENERGÍA EN AUTOCONSUMO COLECTIVO CON EXCEDENTES Y COMPENSACIÓN")}</h1>
    </div>
    <p>
        ${_(u"En aplicación del Real Decreto 244/2019, de 5 de abril, los siguientes consumidores acordamos asociarnos en una instalación de autoconsumo colectivo de energía eléctrica con las siguientes características:")}
    </p>
    <p>
        <input type="checkbox"> ${_(u"CON excedentes acogidos a compensación simplificada")}</input>
    </p>
    <p>
        <input type="checkbox"> ${_(u"CON excedentes no acogidos a compensación simplificada")}</input>
    </p>
    <p>
        <b> ${_(u"Código de autoconsumo (CAU):")} </b>
    </p>
    <p>
        ${_(u"(completar por cada consumidora asociada)")}
    </p>
    <table>
        <thead>
            <tr>
                <th colspan="2">
                    ${_("<b>Productora asociada</b> (titular de la instalación de generación)")}
                </th>
                <th>
                    ${_("NIF")}
                </th>
                <th>
                    ${_("CIL")}
                </th>
                <th>
                    ${_("Coefieciente (α)")}
                </th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>
                    1
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
            </tr>
        </tbody>
    </table>

    <br/>

    <table>
        <thead>
            <tr>
                <th colspan="2">
                    ${_("<b>Consumidora asociada</b> (titular del suministro)")}
                </th>
                <th>
                    ${_("NIF")}
                </th>
                <th>
                    ${_("CUPS")}
                </th>
                <th>
                    ${_("Coeficiente de Reparto (ß)")}
                </th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
            </tr>
        </tbody>
    </table>

    <p style="page-break-after:always"></p>
    <br/> <br/> <br/>

    ${_(u"Con la firma de este acuerdo:")}
    <ul>
        <li>
            ${_(u"En el caso de que la instalación esté dada de alta en la modalidad con excedentes acogida a compensación, las personas consumidoras nos acogemos voluntariamente al mecanismo de compensación simplificada entre los déficits de consumo de cada una y la totalidad de los excedentes de la instalación de autoconsumo, la generación eléctrica neta se repartirá de acuerdo con los coeficientes de reparto (β) indicados, tal y como establece el Real Decreto 244/2019, de 5 de abril.")}
        </li>
        <li>
            ${_(u"Las personas consumidoras manifiestan que SOM ENERGIA, SCCL, actúa como gestor y titular de los derechos de explotación propios de la Instalación, legalizados en régimen de autoconsumo colectivo con excedentes. Especialmente en el caso de estar acogidas a la modalidad de autoconsumo con excedentes sin compensación simplificada, las Partes asumen y entienden que la energía producida por la Instalación que, por falta de consumo horario suficiente del CUPS asociado no puede ser considerada energía horaria autoconsumida, corresponde en exclusiva a la titular de la Instalación, tanto su propiedad como su valoración, formas de aprovechamiento y en general cualquier otro aspecto relativo a esta energía.")}
        </li>
        <li>
            ${_(u"Todas las partes nos obligamos a notificar este acuerdo de reparto a la compañía comercializadora con la que tenemos contratado el suministro eléctrico, con la instrucción de realizar todos los trámites necesarios para modificar el Contrato Técnico de Acceso a redes suscrito con la propietaria de la red, a fin de activar el autoconsumo colectivo y aplicar del presente acuerdo de reparto, en particular el mecanismo de compensación simplificada de los excedentes de la instalación de autoconsumo a la que nos asociamos y el inicio del mecanismo de compensación en el siguiente periodo de facturación desde la recepción de este acuerdo, en los términos previstos en el Real Decreto 244/2019 y la normativa que lo desarrolla.")}
        </li>
        <li>
            ${_(u"La productora asociada se compromete a informar a las consumidoras, directamente o a través del gestor de este autoconsumo colectivo (SOM ENERGIA, SCCL), de cualquier incidencia que afecte a la instalación.")}
        </li>
        <li>
            ${_(u"Todas las partes, tanto productora asociada como consumidoras, se obligan a mantener absoluta confidencialidad sobre los datos personales a los que tienen acceso con motivo de la firma de este acuerdo de reparto.")}
        </li>
        <li>
            ${_(u"Todas las partes, tanto Productora Asociada como Consumidoras, aceptan expresamente la cesión de los datos personales recogidos en este documento al resto de participantes, a sus respectivas comercializadoras, a la distribuidora propietaria de la red a la que se conectan, a las autoridades competentes, a la empresa instaladora o mantenedora de la instalación asociada y a Som Energia, SCCL, como gestora de la instalación asociada, con la sola finalidad de gestionar y tramitar la aplicación del presente acuerdo de reparto y del autoconsumo colectivo al que se refiere.")}
        </li>
        <li>
            ${_(u"Todas las partes quedan informadas de que el responsable del tratamiento de los datos personales objeto de la cesión es Som Energia, SCCL, en cuanto que actúa como representante del autoconsumo colectivo, con el fin de gestionar y tramitar la aplicación del presente acuerdo de reparto y del autoconsumo colectivo al que hace referencia. Por lo tanto, salvo la obligada cesión indicada, los datos no serán cedidos, excepto en los supuestos legalmente exigidos, y solo se conservarán mientras el titular de los datos esté asociado al autoconsumo colectivo y, una vez finalizada esta pertenencia, dentro de los plazos legales previstos.")}
        </li>
        <li>
            ${_(u"Se puede retirar el consentimiento en cualquier momento y ejercer el derecho de acceso, rectificación, supresión, portabilidad, limitación y oposición dirigiéndose a somenergia@delegado-datos.com (delegado de protección de datos). En caso de divergencias, se puede presentar una reclamación ante la Agencia de Protección de Datos (www.aepd.es).")}
        </li>
    </ul>
    <p style="page-break-after:always"></p>
    <p>A Girona, ... de ... de ...</p>
    <p>${_(u"Las CONSUMIDORAS asociadas representadas por su representante SOM ENERGIA Sccl con NIF F55091367")}</p>
    <p>&nbsp;</p>
    <br/>
    <br/>
    <p>&nbsp;</p>
</%def>
