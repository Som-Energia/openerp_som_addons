<%page args="d" />
<li>
    ${_(u"El %s la distribuïdora (%s) ens envia el cas ATR D1 01 amb la següent informació:") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> D1 (Autoconsum)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Motiu canvi:</b> %s") % (d.motiu_canvi)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>CAU:</b> %s") % (d.CAU)}<br/>
    %if d.seccio_registre:
        ${_(u"<b>Secció Registre:</b> %s") % (d.seccio_registre)}<br/>
    %endif
    ${_(u"<b>Subsecció:</b> %s") % (d.subseccio)}<br/>
    ${_(u"<b>CUPS:</b> %s") % (d.CUPS)}<br/>
    % for gen in d.generadors:
        ${_("<b>Potència instal·lada: </b> %s") % (gen['potencia_instalada'])} <br/>
        ${_("<b>Tecnologia Generador: </b> %s") % (gen['tec_generador'])} <br/>
        ${_("<b>Tipus Instal·lació: </b> %s") % (gen['tipus_instalacio'])} <br/>
        %if gen['SSAA'] == 'S':
            ${_("<b>SSAA: </b>Sí")} <br/>
        %else:
            ${_("<b>SSAA: </b>No")} <br/>
        %endif
        ${_("<b>Ref cadastre Instal·lació: </b> %s") % (gen['ref_cadastre'])} <br/>
        ${_("<b>Nom de la persona o societat: </b> %s") % (gen['nom'])} <br/>
        ${_("<b>Primer cognom: </b> %s") % (gen['cognom1'])} <br/>
        ${_("<b>Segon cognom: </b> %s") % (gen['cognom2'])} <br/>
        ${_("<b>Tipus document: </b> %s") % (gen['tipus_document'])} <br/>
        ${_("<b>Document: </b> %s") % (gen['document'])} <br/>
        ${_("<b>Email: </b> %s") % (gen['email_contacte'])} <br/>
    % endfor
    % if d.comentaris != '':
        ${_(u"<b>Comentaris:</b> %s") % (d.comentaris)}<br/>
    %endif
    <br><br>
</li>
