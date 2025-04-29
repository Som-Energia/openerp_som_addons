<%def name="gurb_baixa_ca()">
<p style="page-break-after:always;"></p>
<br>
<br>
<div id="titol">
    <h2 style="font-size: 14px;">Annex III</h2>
</div>

<div class="content_generals">
    <h3 style="text-align: center;">
        Confirmació de baixa en autoconsum col·lectiu
    </h3>
    <br />
    % if not informe["is_enterprise"]:
        <p>
            ${informe['name']}, major d'edat, amb domicili a ${informe['address']} i DNI número ${informe['nif']}, de forma lliure i voluntària i en ple ús de les meves facultats, i en tant que titular del CUPS ${informe['cups']}.
        </p>
    % else:
        <p>
            ${informe["representative"]["name"]}, major d'edat, amb NIF número ${informe["representative"]["vat"]} i domicili a ${informe["representative"]["address"]}, actuant en la meva condició de REPRESENTANT, i manifestant que en aquesta condició disposo de les facultats suficients, actuant EN NOM I REPRESENTACIÓ DE ${informe["name"]} , amb NIF ${informe['nif']} i domicili social a ${informe['address']} com a titular del CUPS ${informe['cups']}.
        </p>
    % endif
    <p>
        CONFIRMO que tant en el cas de la resolució del Contracte de Subministrament amb SOM ENERGIA, SCCL, com en el cas de la meva baixa del GURB, segons preveuen les seves Condicions Específiques, deixaré de formar part de l’autoconsum col·lectiu CAU que se m’hagi assignat per part de la distribuïdora i notificat per part de SOM ENERGIA, SCCL, a través de correu electrònic; per tant, autoritzo SOM ENERGIA, SCCL, com a representant d’aquest autoconsum col·lectiu, i en particular Núria Palmada García o qualsevol altra persona apoderada de SOM ENERGIA, SCCL, a fer tots els tràmits necessaris per gestionar-ne la modificació.
    </p>
    <br />
    <p>
        Girona, ${informe['day']} ${informe['month']} de ${informe['year']}
    </p>
    <br />
    <p>
        L'Autoritzant
    </p>
    <br />
    <br />
    <p>
        ${informe['name']} ${informe['nif']}
    </p>
</div>
</%def>

<%def name="gurb_baixa_es()">
<p style="page-break-after:always;"></p>
<br>
<br>
<div id="titol">
    <h2 style="font-size: 14px;">Anexo III</h2>
</div>

<div class="content_generals">
    <h3 style="text-align: center;">
        Confirmación de baja en autoconsumo colectivo
    </h3>
    <br />
    % if not informe["is_enterprise"]:
        <p>
            ${informe['name']}, mayor de edad, con domicilio en ${informe['address']} y DNI número ${informe['nif']}, de forma libre y voluntaria y en pleno uso de mis facultades, y como titular del CUPS ${informe['cups']}.
        </p>
    % else:
        <p>
            ${informe["representative"]["name"]}, mayor de edad, con NIF número ${informe["representative"]["vat"]} y domicilio en ${informe["representative"]["address"]}, actuando en mi condición de REPRESENTANTE, y manifestando que en esta condición dispongo de las facultades suficientes, actuando en NOMBRE Y REPRESENTACIÓN DE ${informe["name"]}, con NIF ${informe['nif']} y domicilio social en ${informe['address']} como titular del CUPS ${informe['cups']}.
        </p>
    % endif
    <p>
        CONFIRMO que tanto en el caso de la resolución del Contrato de Suministro con SOM ENERGIA, SCCL, como  en el caso de mi baja del GURB, según prevén sus Condiciones Específicas, dejaré de formar parte del autoconsumo colectivo CAU que se me haya asignado por parte de la distribuidora y notificado por parte de SOM ENERGIA, SCCL, a través de correo electrónico; por lo tanto, autorizo a SOM ENERGIA, SCCL, como representante de este autoconsumo colectivo, y en particular a Núria Palmada García o cualquier otra persona apoderada de SOM ENERGIA, SCCL, a hacer todos los trámites necesarios para tramitar su modificación.
    </p>
    <br />
    <p>
        Girona, ${informe['day']} ${informe['month']} de ${informe['year']}
    </p>
    <br />
    <p>
        El Autorizante
    </p>
    <br />
    <br />
    <p>
        ${informe['name']} ${informe['nif']}
    </p>
</div>
</%def>
