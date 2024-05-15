## -*- coding: utf-8 -*-
<%def name="resum_facturacio_anual(costs)">
    <div class="seccio container-resum">
        <span>${_(u"RESUM DE LA TEVA FACTURACIÓ ANUAL")}</span>
        <hr/>
    </div>
    <div class="container">
        <div class="dades-resum">
            <table>
                <colgroup>
                    <col width="70%"/>
                    <col width="30%"/>
                </colgroup>
                <tr>
                    <td>
                        <p><b>${_(u"Cost de l'electricitat utilitzada:")}</b></p>
                        <p class="secondary-text">${_(u"Oferim 2 tarifes diferents:")} <a href="${_(u"https://www.somenergia.coop/ca/tarifes-delectricitat-que-oferim/tarifa-periodes/")}">${_(u"períodes")}</a> ${_(u"i")} <a href="${_(u"https://www.somenergia.coop/ca/tarifes-delectricitat-que-oferim/tarifa-indexada/")}">${_(u"indexada")}</a>.</p>
                    </td>
                    <td><b><span style="color: #4d4d4d">${costs['energia']} €</span></b></td>
                </tr>
                <tr>
                    <td>
                        <p><b>${_(u"Cost de les potències contractades:")}</b></p>
                        <p class="secondary-text">${_(u"Correspon íntegrament als costos regulats, ja que no hi afegim marge per la cooperativa.")}</p>
                    </td>
                    <td><b><span style="color: #80a82d">${costs['potencia']} €</span></b></td>
                </tr>
                <tr>
                    <td>
                        <p><b>${_(u"Cost de l'excés de potència:")}</b></p>
                        <p class="secondary-text">${_(u"També regulat. L'analitzem a continuació junt amb el cost de les potències contractades.")}</p>
                    </td>
                    <td><b><span style="color: #c7d1b0">${costs['exces']} €</span></b></td>
                </tr>
                <tr>
                    <td>
                        <p><b>${_(u"Cost de l'energia reactiva:")}</b></p>
                        <p class="secondary-text">${_(u"A partir de 400 € recomanem la instal·lació de bateries de condensadors.")} <a href="${_(u"https://ca.support.somenergia.coop/article/259-energia-reactiva-que-es-efectes-en-la-factura-i-com-eliminar-la")}">${_(u"Més informació.")}</a></p>
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
                        <p class="text-descompte">${_(u"Descompte pels excedents:")}</p>
                        <p class="secondary-text text-negre">${_(u"Inclou la compensació i el Flux Solar descomptats.")}</p>
                    </td>
                    <td class="text-descompte"><b>${costs['descompte_generacio']} €</b></td>
                </tr>
            </table>
        </div>
    </div>
    <div class="container">
        <div class="note">
            <span>
                ${_(u"No incloem el lloguer del comptador i els impostos. Dades dels últims 12 mesos facturats.")}
            </span>
        </div>
    </div>
    <div class="container alert">
        <div class="exclamation">
            <span><b>!</b></span>
        </div>
        <div>
            <p class="alert-text">
                ${_(u"Pots consultar i descarregar les corbes horàries d'ús d'energia per dies, setmanes, mesos i anys, i fer comparatives entre aquests períodes a l'")}<a href="${_(u"https://oficinavirtual.somenergia.coop/ca/")}">${_(u"Oficina Virtual")}</a>, <b>${_(u"a l'apartat Infoenergia > Veure l'ús de l'energia")}</b>.
            </p>
        </div>
    </div>
</%def>
