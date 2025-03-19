<%page args="d" />
<li>
    ${_(u"El %s Som Energia presenta una reclamació a la distribuïdora (%s):") % (d.day, d.distribuidora) }<br/>
    <br>
    ${_(u"<b>Procediment:</b> R1 (reclamació)")}<br/>
    ${_(u"<b>Pas:</b> 01")}<br/>
    ${_(u"<b>Tipus de reclamació:</b> %s") %(d.tipus_reclamacio)}<br/>
    ${_(u"<b>Codi de la sol·licitud:</b> %s") % (d.codi_solicitud)}<br/>
    ${_(u"<b>Data creació:</b> %s") % (d.create)}<br/>
    % if len(d.variables_aportacio):
        ${_(u"<b>Variables d'aportació:</b> %s variable(s)") % (str(len(d.variables_aportacio)))}<br/>
        % for var_apo in d.variables_aportacio:
            % if var_apo['descripcio']:
                ${_(' - <b>%s:</b> %s  tipus: <i>%s</i>  descripció: <i>%s</i>') % (var_apo['variable'], var_apo['valor'], var_apo['tipus'], var_apo['descripcio'])}<br/>
            % else:
                ${_(' - <b>%s:</b> %s  tipus: <i>%s</i>') % (var_apo['variable'], var_apo['valor'], var_apo['tipus'])}<br/>
            % endif
        % endfor
    %endif
    %for reclama in d.reclamacions:

        ${_(u"<b>Detalls Reclamació:</b>")}<br/>
        %if reclama['codi_dh']:
            ${_(u"&nbsp;&nbsp;Codi dh: %s") %(reclama['codi_dh'])}<br/>
        %endif
        %if reclama['codi_incidencia']:
            ${_(u"&nbsp;&nbsp;Codi incidència: %s") %(reclama['codi_incidencia'])}<br/>
        %endif
        %if reclama ['codi_postal']:
            ${_(u"&nbsp;&nbsp;Codi postal: %s") %(reclama ['codi_postal'])}<br/>
        %endif
        %if reclama['codi_solicitud']:
            ${_(u"&nbsp;&nbsp;Codi sol·licitud: %s") %(reclama['codi_solicitud'])}<br/>
        %endif
        %if reclama['codi_solicitud_reclamacio']:
            ${_(u"&nbsp;&nbsp;Codi sol·licitud reclamació: %s") %(reclama['codi_solicitud_reclamacio'])}<br/>
        %endif
        %if reclama['concepte_disconformitat']:
            ${_(u"&nbsp;&nbsp;Concepte disconformitat: %s") %(reclama['concepte_disconformitat'])}<br/>
        %endif
        %if reclama['cont_email']:
            ${_(u"&nbsp;&nbsp;Cont email: %s") %(reclama['cont_email'])}<br/>
        %endif
        %if reclama['cont_nom']:
            ${_(u"&nbsp;&nbsp;Cont nom: %s") %(reclama['cont_nom'])}<br/>
        %endif
        %if reclama['cont_prefix']:
            ${_(u"&nbsp;&nbsp;Cont prefix: %s") %(reclama['cont_prefix'])}<br/>
        %endif
        %if reclama['cont_telefon']:
            ${_(u"&nbsp;&nbsp;Cont telèfon: %s") %(reclama['cont_telefon'])}<br/>
        %endif
        %if reclama['data_fins']:
            ${_(u"&nbsp;&nbsp;Data fins: %s") %(reclama['data_fins'])}<br/>
        %endif
        %if reclama['data_incident']:
            ${_(u"&nbsp;&nbsp;Data incident: %s") %(reclama['data_incident'])}<br/>
        %endif
        %if reclama['data_inici']:
            ${_(u"&nbsp;&nbsp;Data inici: %s") %(reclama['data_inici'])}<br/>
        %endif
        %if reclama['data_lectura']:
            ${_(u"&nbsp;&nbsp;Data lectura: %s") %(reclama['data_lectura'])}<br/>
        %endif
        %if reclama['descripcio_ubicacio']:
            ${_(u"&nbsp;&nbsp;Descripció ubicació: %s") %(reclama['descripcio_ubicacio'])}<br/>
        %endif
        %if reclama['IBAN']:
            ${_(u"&nbsp;&nbsp;IBAN: %s") %(reclama['IBAN'])}<br/>
        %endif
        %if reclama['import_reclamat']:
            ${_(u"&nbsp;&nbsp;Import reclamat: %s") %(reclama['import_reclamat'])}<br/>
        %endif
        %if reclama['municipi']:
            ${_(u"&nbsp;&nbsp;Municipi: %s") %(reclama['municipi'])}<br/>
        %endif
        %if reclama['numero_expedient_escomesa']:
            ${_(u"&nbsp;&nbsp;Número expedient escomesa: %s") %(reclama['numero_expedient_escomesa'])}<br/>
        %endif
        %if reclama['numero_expedient_frau']:
            ${_(u"&nbsp;&nbsp;Número expedient frau: %s") %(reclama['numero_expedient_frau'])}<br/>
        %endif
        %if reclama['numero_factura']:
            ${_(u"&nbsp;&nbsp;Número factura: %s") %(reclama['numero_factura'])}<br/>
        %endif
        %if reclama['parametre_contractacio']:
            ${_(u"&nbsp;&nbsp;Paràmetre contractació: %s") %(reclama['parametre_contractacio'])}<br/>
        %endif
        %if reclama['poblacio']:
            ${_(u"&nbsp;&nbsp;Població: %s") %(reclama['poblacio'])}<br/>
        %endif
        %if reclama['provincia']:
            ${_(u"&nbsp;&nbsp;Província: %s") %(reclama['provincia'])}<br/>
        %endif
        %if reclama['tipus_atencio_incorrecte']:
            ${_(u"&nbsp;&nbsp;Tipus atenció incorrecte: %s") %(reclama['tipus_atencio_incorrecte'])}<br/>
        %endif
        %if reclama['tipus_concepte_facturat']:
            ${_(u"&nbsp;&nbsp;Tipus concepte facturat: %s") %(reclama['tipus_concepte_facturat'])}<br/>
        %endif
        % if reclama['lectures']:
            ${_(u"&nbsp;&nbsp;Lectures:")}<br/>
            % for lectures in reclama['lectures']:
                ${_(u"&nbsp;&nbsp;lectura: %s") %(lectures['lectura'])}<br/>
                ${_(u"&nbsp;&nbsp;magnitud: %s") %(lectures['magnitud'])}<br/>
                ${_(u"&nbsp;&nbsp;nom: %s") %(lectures['nom'])}<br/>
            % endfor
        % endif
    % endfor
    % if len(d.documents_adjunts) > 0:
        ${_(u"<b>Documents adjunts:</b> Si")}<br/>
        ${_(u"<b>Tipus de document:</b>")}<br/>
        % for doc in d.documents_adjunts:
             ${_(' - %s, <a href="%s">enllaç al document</a>') % (doc[0], doc[1])}<br/>
        % endfor
    % else:
        ${_(u"<b>Documents adjunts:</b> No")}<br/>
    % endif
    % if d.text:
        ${_(u"<b>Text de la reclamació:</b> <i>%s</i>") % (d.text)}<br/>
    %endif
     <br/>
</li>
