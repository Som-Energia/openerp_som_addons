<%def name="gurb_autoritzacio_ca(gurb)">
<% informe = gurb["annex"] %>
<p style="page-break-after:always;"></p>
<br>
<br>
<div id="titol">
    <h2 style="font-size: 14px;">Annex II</h2>
</div>
<div id="titol">
    <h2 style="font-size: 14px;">Autorització del representant de l'autoconsum col·lectiu</h2>
</div>

<div class="content_generals">
    <p>
        Atès el que preveu la normativa sectorial aplicable i en particular els articles 9 i 44 de la Llei 24/2013; els articles 3, 4, 16 bis de l'Annex I del RD 244/2019; i la disposició transitòria segona de l'Ordre TED /1247/2021, així com els principis generals, en particular el de llibertat de forma, i els articles 1710 i 1280 del Codi Civil Espanyol.
    </p>
    %if informe['is_enterprise']:
        <p>
            ${informe["representative"]["name"]}, major d'edat, amb NIF número ${informe["representative"]['vat']} i domicili a ${informe["representative"]["address"]}, actuant en la meva condició de REPRESENTANT, i manifestant que en aquesta condició disposo de les facultats suficients, actuant EN NOM I REPRESENTACIÓ DE ${informe["name"]} , amb NIF ${informe['nif']} i domicili social a ${informe['address']} com a titular del CUPS ${informe['cups']} (“Autoritzant”)
        </p>
    %else:
        <p>
            ${informe['name']}, major d'edat, amb domicili a ${informe['address']} i DNI número ${informe['nif']}, de forma lliure i voluntària i en ple ús de les meves facultats, i en tant que titular del CUPS ${informe['cups']} associat a l'autoconsum col·lectiu CAU ${informe["cau"]} (“Autoritzant”)
        </p>
    %endif
    <p>
        <b> AUTORITZO: </b>
    </p>
    <p>
        SOM ENERGIA, SCCL, amb NIF F55091367 i domicili social al carrer  Riu Güell 68, 17005 Girona (“Autoritzada”) a actuar com a representant  integral del meu CUPS en tant que associat a l'autoconsum col·lectiu CAU provisional ${informe["cau"]}, per termini il·limitat, a fi que pugui dur a terme les ACTUACIONS següents:
    </p>
    <ul>
        <li>
            Signar en nom meu l’acord de repartiment que reculli els coeficients de repartiment pels quals s'assignen coeficients de repartiment a CUPS de la meva titularitat, així com qualsevol modificació d'aquests acords.
        </li>
        <li>
            Comunicar directament en nom meu aquest acord de repartiment (i les seves modificacions), així com el fitxer de coeficients de repartiment corresponent a l'empresa distribuïdora propietària de la xarxa a la qual em connecto, així com a l'empresa comercialitzadora amb què tingui en cada moment contractat el subministrament elèctric.
        </li>
        <li>
            Fer en nom meu qualsevol gestió o comunicació amb la distribuïdora que sigui necessària, convenient, accessòria o relacionada amb l'aplicació del terme de descompte per retard en activació d'autoconsum (art. 16.bis Reial decret 244/2019).
        </li>
        <li>
            Recepcionar i ventilar en nom meu, per qualsevol via, qualsevol comunicació necessària, convenient, accessòria o relacionada amb les actuacions indicades més amunt, incloent-hi aquelles per les quals es tractin o comparteixin els acords de repartiment o les seves modificacions, sigui amb la distribuïdora, l'Autoritzada o altres signants, presents o futurs.
        </li>
        <li>
            Cedir les meves dades personals recollides en aquest document a la resta de participants en l'autoconsum col·lectiu CAU provisional ${informe["cau"]}, a les seves respectives comercialitzadores, a la distribuïdora propietària de la xarxa a la qual es connectin, a les autoritats competents, a l'empresa instal·ladora o mantenidora de la instal·lació associada, amb la sola finalitat de gestionar i tramitar l'aplicació de l'acord de repartiment i l'activació, modificació o baixa de l'autoconsum col·lectiu al qual fa referència.
        </li>
    </ul>
    <p>
        Llevat l'obligada cessió indicada, declaro que conec que Som Energia, SCCL, és la responsable del tractament de les dades personals objecte d'aquesta autorització, que m'ha informat clarament que les dades no seran cedides, excepte en els supòsits legalment exigits, que només es conservaran mentre la present autorització estigui vigent i, una vegada finalitzada aquesta, dins dels terminis legals previstos. Així mateix, declaro que Som Energia, SCCL, m'ha informat que puc retirar el meu consentiment en qualsevol moment i exercir el meu dret d'accés, rectificació, supressió, portabilitat, limitació i oposició dirigint-me a somenergia@delegado-datos.com (delegat de protecció de dades). En cas de divergències, puc presentar una reclamació davant l'Agència de Protecció de Dades (www.aepd.es).
    </p>
    <ul>
        <li>
            A dur a terme qualsevol altra actuació que, segons el parer de l'Autoritzada, sigui necessària, convenient, accessòria o relacionada amb les actuacions indicades més amunt.
        </li>
    </ul>
    <p> Girona, ${informe['day']}/${informe['month']}/${informe['year']}</p>
    <p>L'Autoritzant</p>
    <p>${informe['name']} ${informe['nif']}</p>
</div>
</%def>

<%def name="gurb_autoritzacio_es(gurb)">
<% informe = gurb["annex"] %>
<p style="page-break-after:always;"></p>
<br>
<br>
<div id="titol">
    <h2 style="font-size: 14px;">Annexo II</h2>
</div>
<div id="titol">
    <h2 style="font-size: 14px;">Autorización al representante del autoconsumo colectivo</h2>
</div>

<div class="content_generals">
    <p>
        Visto lo que prevé la normativa sectorial aplicable y en particular los artículos 9 y 44 de la Ley 24/2013; los artículos 3, 4, 16 bis del Anexo I del RD 244/2019; la disposición transitoria segunda de la Orden TED /1247/2021, así como los principios generales, en particular el de libertad de forma, y los artículos 1710 y 1280 del Código Civil Español.
    </p>
    %if informe['is_enterprise']:
        <p>
            ${informe["representative"]["name"]}, mayor de edad, con NIF número ${informe["representative"]['vat']} y domicilio en ${informe["representative"]["address"]}, actuando en mi condición de REPRESENTANTE, y manifestando que en esta condición dispongo de las facultades suficientes, actuando en NOMBRE Y REPRESENTACIÓN DE ${informe["name"]}, con NIF ${informe['nif']} y domicilio social en ${informe['address']} como titular del CUPS ${informe['cups']} (“Autorizante”)
        </p>
    %else:
        <p>
            ${informe['name']}, mayor de edad, con domicilio en ${informe['address']} y DNI número ${informe['nif']}, de forma libre y voluntaria y en pleno uso de mis facultades, y como titular del CUPS ${informe['cups']} asociado al autoconsumo colectivo CAU ${informe["cau"]} (“Autorizante”)
        </p>
    %endif
    <p>
        <b> AUTORIZO A: </b>
    </p>
    <p>
        SOM ENERGIA, SCCL, con NIF F55091367 y domicilio social en la calle Riu Güell 68, 17005 Girona (“Autorizada”) a actuar como representante integral del mi CUPS como asociado al autoconsumo colectivo CAU provisional ${informe["cau"]}, por plazo ilimitado, a fin de que pueda realizar las siguientes ACTUACIONES:
    </p>
    <ul>
        <li>
            Firmar en mi nombre el acuerdo de reparto que recoja los coeficientes de reparto por los que se asignan coeficientes de reparto a CUPS de mi titularidad, así como cualquier modificación de estos acuerdos.
        </li>
        <li>
            Comunicar directamente en mi nombre este acuerdo de reparto (y sus modificaciones), así como el fichero de coeficientes de reparto correspondiente a la empresa distribuidora propietaria de la red a la que me conecto y a la empresa comercializadora con la que tenga en cada momento contratado el suministro eléctrico.
        </li>
        <li>
            Realizar en mi nombre cualquier gestión o comunicación con la distribuidora que sea necesaria, conveniente, accesoria o relacionada con la aplicación del término de descuento por retraso en activación de autoconsumo (art. 16.bis del Real Decreto 244/2019).
        </li>
        <li>
            Recepcionar y ventilar en mi nombre, por cualquier vía, cualquier comunicación necesaria, conveniente, accesoria o relacionada con las actuaciones arriba indicadas, incluidas aquellas por las que se traten o compartan los acuerdos de reparto o sus modificaciones, sea con la distribuidora, la Autorizada u otros firmantes, presentes o futuros.
        </li>
        <li>
            Ceder mis datos personales recogidos en este documento al resto de participantes en el autoconsumo colectivo CAU provisional ${informe["cau"]}, a sus respectivas comercializadoras, a la distribuidora propietaria de la red a la que se conecten, a las autoridades competentes, a la empresa instaladora o mantenedora de la instalación asociada, con la sola finalidad de gestionar y tramitar la aplicación del acuerdo de reparto y la activación, modificación o baja del autoconsumo colectivo al que hace referencia.
        </li>
    </ul>
    <p>
        Salvo la obligada cesión indicada, declaro que conozco que Som Energia, SCCL, es la responsable del tratamiento de los datos personales objeto de esta autorización, que me ha informado claramente de que los datos no serán cedidos, excepto en los supuestos legalmente exigidos, que solo se conservarán mientras la presente autorización esté vigente y, una vez finalizada esta, dentro de los plazos legales previstos. Así mismo, declaro que Som Energia, SCCL, me ha informado de que puedo retirar mi consentimiento en cualquier momento y ejercer mi derecho de acceso, rectificación, supresión, portabilidad, limitación y oposición dirigiéndome a  somenergia@delegado-datos.com (delegado de protección de datos). En caso de divergencias, puedo presentar una reclamación ante la Agencia de Protección de Datos (www.aepd.es).
    </p>
    <ul>
        <li>
            A realizar cualquier otra actuación que, según el parecer de la Autorizada, sea necesaria, conveniente, accesoria o relacionada con las actuaciones antes indicadas.
        </li>
    </ul>
    <p> Girona, ${informe['day']}/${informe['month']}/${informe['year']}</p>
    <p>El Autorizante</p>
    <p>${informe['name']} ${informe['nif']}</p>
</div>
</%def>
