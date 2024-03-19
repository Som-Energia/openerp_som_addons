<%def name="analisi_potencies(potencia)">
    <div class="seccio">
        <span>
            ${_(u"ANÀLISI DE LES POTÈNCIES CONTRACTADES I ESTIMACIÓ DEL COST TOTAL")}
        </span>
        <hr/>
    </div>
    <div>
        <table class="taula-potencies">
            <tr>
                <th></th>
                <th>
                    <b>${_(u"Potències actuals")}</b>
                </th>
                <th>
                    <b>${_(u"Potències òptimes")}</b>
                </th>
                <th colspan="12">
                    <b>${_(u"Potència màxima registrada")}</b>
                </th>
            </tr>
            <% it = 0 %>
            %for potencia_contractada in potencia['potencies_contractades']:
                <%
                    from dateutil.relativedelta import relativedelta
                    from datetime import datetime

                    periode = 'P{}'.format(it+1)
                    any_anterior = (datetime.now() - relativedelta(years=+2)).year
                %>
                <tr>
                    <td>${periode}</td>
                    <td>${potencia_contractada}</td>
                    <td>
                        ${potencia['optimizations']['optimal_powers_{}'.format(periode.upper())]}
                    </td>

                    %for mes in range(1, 13):
                        <%
                            mesany = '%02d%s' % (mes, any_anterior)
                        %>
                        %if potencia['maximetres'].get(mesany):
                            <td>${potencia['maximetres'][mesany][periode]}</td>
                        %else:
                            <td>-</td>
                        %endif
                    %endfor
                </tr>
                <% it += 1 %>
            %endfor
            <tr>
                <td colspan="3">${_(u"Tots els valors es mostre en kW")}</td>
                <td>${_(u"GEN")}</td>
                <td>${_(u"FEB")}</td>
                <td>${_(u"MAR")}</td>
                <td>${_(u"ABR")}</td>
                <td>${_(u"MAI")}</td>
                <td>${_(u"JUN")}</td>
                <td>${_(u"JUL")}</td>
                <td>${_(u"AGO")}</td>
                <td>${_(u"SET")}</td>
                <td>${_(u"OCT")}</td>
                <td>${_(u"NOV")}</td>
                <td>${_(u"DES")}</td>
            </tr>
        </table>
    </div>
    <div class="container">
    <span class="text-estimacio">${_(u"Les potències òptimes proposades minimitzen el cost anual total de potència i són vàlides si es manté un ús similar d’energia en les mateixes hores.")}</span>
    </div>
    <div class="container">
        <div class="estimacio">
            ${_(u"Estimació del cost anual")} <span class="subratllar">${_(u"amb les potències actuals")}</span>:<br />${potencia['estimacio_cost_potencia_actual']} €
        </div>
        <div class="estimacio">
            ${_(u"Estimació del cost anual")} <span class="subratllar">${_(u"amb les potències òptimes")}</span>:<br />${potencia['estimacio_cost_potencia_optima']} €
        </div>
        <div class="estimacio">
            <a href="${_(u"https://ca.support.somenergia.coop/article/271-com-puc-fer-una-modificacio-de-potencia-o-de-tarifa-i-quant-costa")}">${_(u"Més informació per modificar les potències contractades</a>")}
        </div>
    </div>
    <hr/>
</%def>
