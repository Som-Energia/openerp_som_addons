<%def name="summary_discounts(discounts)">
<div class="summary-box">
    <h3>${_(u"5. Descomptes i promocions")}</h3>
    <div class="summary-content">
        %if discounts['show_legal_text']:
            <p class="section-text">${_(u"En cas que se t'apliqui el descompte flux solar, s'informarà d'aquest descompte a la factura següent a aquella en la qual no hagi estat possible compensar tot el valor econòmic dels excedents de la instal·lació d'autoconsum. En cap cas podrà ser superior al 80% del valor dels excedents informats per l'encarregat de lectura i que no hagi estat possible compensar, ni tampoc podrà superar el valor de la factura.")}</p>
            <p class="section-text">${_(u"En cas que et quedin SOLS pendents d'aplicar i que et donin dret al descompte, aquests caducaran cinc anys després de la data de factura on consta la seva emissió.")}</p>
            <p class="section-text">${_(u"En cas que donis de baixa del punt de subministrament, de canvi de comercialitzadora, de traspàs o subrogació del contracte, els SOLS i els descomptes pendents d'aplicació es perdran automàticament.")}</p>
        %else:
            <p class="section-text">N/A</p>
        %endif
    </div>
</div>
</%def>
