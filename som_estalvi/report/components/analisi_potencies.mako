<%def name="analisi_potencies(potencia)">
    <div class="seccio">
        <span>
            ANÀLISI DE LES POTÈNCIES CONTRACTADES I ESTIMACIÓ DEL COST TOTAL
        </span>
        <hr/>
    </div>
    <div>
        <table class="taula-potencies">
            <tr>
                <th></th>
                <th>
                    <b>Potències actuals</b>
                </th>
                <th>
                    <b>Potències òptimes</b>
                </th>
                <th colspan="12">
                    <b>Potència màxima registrada</b>
                </th>
            </tr>
            <% it = 0 %>
            %for potencia in potencia['potencies_contractades']:
                <tr>
                    <td>P${it+1}</td>
                    <td>${potencia}</td>
                    <td>P1_opt</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                    <td>x</td>
                </tr>
                <% it += 1 %>
            %endfor
            <tr>
                <td colspan="3">Tots els valors es mostre en kW</td>
                <td>GEN</td>
                <td>FEB</td>
                <td>MAR</td>
                <td>ABR</td>
                <td>MAI</td>
                <td>JUN</td>
                <td>JUL</td>
                <td>AGO</td>
                <td>SET</td>
                <td>OCT</td>
                <td>NOV</td>
                <td>DES</td>
            </tr>
        </table>
    </div>
    <div class="container">
    <span class="text-estimacio">Les potències òptimes proposades minimitzen el cost anual total de potència i són vàlides si es manté un ús similar d’energia en les mateixes hores.</span>
    </div>
    <div class="container">
        <div class="estimacio">
            Estimació del cost anual <span class="subratllar">amb les potències actuals</span>:<br />1000€
        </div>
        <div class="estimacio">
            Estimació del cost anual <span class="subratllar">amb les potències òptimes</span>:<br />1000€
        </div>
        <div class="estimacio">
            <a href="https://ca.support.somenergia.coop/article/271-com-puc-fer-una-modificacio-de-potencia-o-de-tarifa-i-quant-costa">Més informació per modificar les potències contractades</a>
        </div>
    </div>
    <hr/>
</%def>
