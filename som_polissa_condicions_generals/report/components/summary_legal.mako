<%def name="summary_legal(features, bono_social_estimate, is_indexed)">
<div class="summary-box">
    <h3>${_(u"6. Durada i pròrroga del contracte")}</h3>
    <div class="summary-content">
        <p class="section-text">${_(u"La durada del contracte és trimestral natural. S'entén per \"trimestre natural\" el període de l'1 de gener al 31 de març, el període de l'1 d'abril al 30 de juny, el període de l'1 de juliol al 30 de setembre i d'1 d'octubre al 31 de desembre.")}</p>
        <p class="section-text">${_(u"Vençut cada període trimestral natural, el contracte es prorrogarà tàcitament i automàticament per períodes trimestrals naturals successius, tret que alguna de les parts comuniqui la seva voluntat de no prorrogar.")}</p>
        <p class="section-text">${_(u"En cas que SOM ENERGIA, SCCL, et comuniqui una modificació substancial del contracte o una revisió del preu aplicable, t'informarà de manera clara i inequívoca ja sigui de les modificacions substancials o del nou preu o condicions econòmiques i, en aquest cas, podràs resoldre el contracte sense penalització en el termini de 15 dies naturals comptats des de la data de la notificació.")}</p>
        %if features['show_section_6_final_paragraph']:
            <p class="section-text">${_(u"En cas que tinguis contractat el servei GURB, anualment s'actualitzarà la quota GURB segons l'Índex de Preus al Consum.")}</p>
        %endif
    </div>
</div>

<div class="summary-box">
    <h3>${_(u"7. Resolució i penalitzacions")}</h3>
    <div class="summary-content">
        <p class="section-text">${_(u"Pots rescindir el teu contracte i les seves pròrrogues en qualsevol moment sens perjudici de les obligacions de pagament per consums efectivament realitzats i, si escau, dels costos que legalment procedeixin. El mateix dret t'aplicarà en cas de modificacions contractuals.")}</p>
        %if features['show_section_7_final_paragraph']:
            <p class="section-text">${_(u"En cas que tinguis contractat el servei GURB o la tarifa Generation kWh, si resols el contracte de subministrament amb tarifa períodes i/o indexada donarà lloc a la baixa automàtica del servei GURB o la tarifa Generation kWh.")}</p>
        %endif
    </div>
</div>

<div class="summary-box">
    <h3>${_(u"8. Dret de desistiment")}</h3>
    <div class="summary-content">
        <p class="section-text">${_(u"Sempre que tinguis la condició de consumidora, segons es defineix en la normativa aplicable, podràs desistir del contracte actual sense necessitat d'al·legar cap causa, en el termini de catorze (14) dies naturals des de la seva celebració, tal com es preveu en la normativa de protecció de persones consumidores i usuàries. La comunicació del desistiment podrà fer-se per correu electrònic, telèfon o correu postal a les adreces indicades en aquest document resum. En cas d'exercici vàlid del desistiment, SOM ENERGIA, SCCL, únicament podrà percebre, si escau, l'import corresponent a l'energia efectivament consumida fins a la data d'eficàcia del desistiment, sense penalització addicional, i d'acord amb la normativa aplicable.")}</p>
    </div>
</div>

%if is_indexed:
    <div class="summary-box">
        <h3>${_(u"9. Informació rellevant sobre la tarifa indexada")}</h3>
        <div class="summary-content">
            <p class="section-text">${_(u"El preu és diferent cada quart d'hora i pot augmentar en períodes d'alta demanda, escassa aportació renovable i/o encariment de la producció amb combustibles fòssils. Si es donen alguna de les condicions anteriors, la teva factura podrà variar de manera rellevant entre mesos.")}</p>
            <p class="section-text">${_(u"Pots estalviar costos adaptant el consum als períodes més econòmics. Així mateix, pots consultar la tendència dels preus a l'enllaç següent.")}</p>
        </div>
    </div>
%endif

</%def>
