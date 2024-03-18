## -*- coding: utf-8 -*-
<%def name="resum_facturacio_anual(costs)">
    <div class="seccio">
        <span>RESUM DE LA TEVA FACTURACIÓ ANUAL</span>
        <hr/>
    </div>
    <div class="container">
        <div class="dades-resum">
            <table>
                <colgroup>
                    <col width="75%"/>
                    <col width="25%"/>
                </colgroup>
                <tr>
                    <td>
                        <p><b>Cost de l'electricitat utilitzada</b></p>
                        <p class="secundary-text">Oferim 2 tarifes diferents: períodes i indexada.</p>
                    </td>
                    <td><b><span style="color: #4d4d4d">${costs['energia']} €</span></b></td>
                </tr>
                <tr>
                    <td>
                        <p><b>Cost de les potències contractades:</b></p>
                        <p class="secundary-text">Correspon íntegrament als costos regulats, ja que no hi afegim marge per la cooperativa.</p>
                    </td>
                    <td><b><span style="color: #80a82d">${costs['potencia']} €</span></b></td>
                </tr>
                <tr>
                    <td>
                        <p><b>Cost de l'excés de potència:</b></p>
                        <p class="secundary-text">També regulat. L'analitzem a continuació junt amb el cost de les potències contractades.</p>
                    </td>
                    <td><b><span style="color: #c7d1b0">${costs['exces']} €</span></b></td>
                </tr>
                <tr>
                    <td>
                        <p><b>Cost per energia reactiva:</b></p>
                        <p class="secundary-text">A partir de 400 € recomanem la instal·lació de bateries de condensadors. <a href="https://ca.support.somenergia.coop/article/259-energia-reactiva-que-es-efectes-en-la-factura-i-com-eliminar-la">Més informació.</a></p>
                    </td>
                    <td><b><span style="color: #71805b">${costs['reactiva']} €</span></b></td>
                </tr>
            </table>
        </div>
        <div class="distribucio-costos">
            <div id="grafic-costos"></div>
        </div>
    </div>
    <div class="container">
        <div class="descomptes-excedents">
            <table>
                <tr>
                    <td>
                        <p class="text-descompte">Descompte pels excedents:</p>
                        <p class="secundary-text text-negre">Inclou la compensació i el Flux Solar.</p>
                    </td>
                    <td class="text-descompte"><b>${costs['descompte_generacio']} €</b></td>
                </tr>
            </table>
        </div>
    </div>
    <div class="container">
        <div class="note">
            <span>
                No s'inclou el lloguer del comptador ni els impostos. Dades dels últims 12 mesos facturats o dels mesos disponibles.
            </span>
        </div>
    </div>
    <div class="container alert">
        <div class="exclamation">
            <span><b>!</b></span>
        </div>
        <div>
            <p class="alert-text">
                Pots consultar i descarregar les corbes horàries d'ús d'energia per dies, setmanes, mesos i anys, i fer comparatives per aquests períodes a l'<a href="https://oficinavirtual.somenergia.coop/ca/">Oficina Virtual</a>, <b>a l'apartat Infoenergia > Veure les corbes horàries</b>.
            </p>
        </div>
    </div>
</%def>
