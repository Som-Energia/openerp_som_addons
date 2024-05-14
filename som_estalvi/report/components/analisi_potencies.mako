<%def name="analisi_potencies(potencia)">
    <div class="seccio">
        <span>
            ${_(u"ANÀLISI DE LES POTÈNCIES CONTRACTADES I ESTIMACIÓ DEL COST ANUAL")}
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
                <th colspan="12" style="text-align: left;">
                    <b>${_(u"Potència màxima registrada")}</b><br/>
                    <span class="secondary-text">${_(u"Si els tres valors del mes corresponen al 85% de la potència contractada, són estimats.")}</span>
                </th>
            </tr>
            <%
                it = 0
                mesos_ordenats = []
                for val in potencia['maximetres'].keys():
                    mesos_ordenats.append(val[2:] + val[:2])
                mesos_ordenats.sort()
            %>
            %for potencia_contractada in potencia['potencies_contractades']:
                <%
                    from dateutil.relativedelta import relativedelta
                    from datetime import datetime

                    periode = 'P{}'.format(it+1)
                %>
                <tr>
                    <td>${periode}</td>
                    <td>${potencia_contractada}</td>
                    <td>
                        ${potencia['optimizations']['optimal_powers_{}'.format(periode.upper())]}
                    </td>

                    %for mes in mesos_ordenats:
                        <% mesany = mes[4:] + mes[:4] %>
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
                <td colspan="3">${_(u"Tots els valors es mostren en kW")}</td>
                %for val in mesos_ordenats:
                    <%
                        mesos = {'01': _('GEN'), '02': _('FEB'), '03': _('MAR'), '04': _('ABR'), '05': _('MAI'), '06': _('JUN'), '07': _('JUL'), '08': _('AGO'), '09': _('SET'), '10': _('OCT'), '11': _('NOV'), '12': _('DES')}
                    %>
                    <td>${mesos[val[4:]]}</td>
                %endfor
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
