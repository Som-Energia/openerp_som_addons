<%page args="invs" />
<style>
<%include file="invoice_summary.css" />
</style>
    <div class="invoice_summary">
        <h1>${_(u"RESUM DE LA FACTURA")}</h1>
        <table>
        <tr><td>${_(u"Per energia utilitzada")}</td><td class="e">${"%s &euro;" % formatLang(invs.total_energy)}</td></tr>
    % if invs.has_autoconsum:
        <tr><td>${_(u"Per energia excedentaria")}</td><td class="e">${"%s &euro;" % formatLang(invs.autoconsum_total_compensada)}</td></tr>
    % endif
        <tr><td>${_(u"Per potència contractada")}</td><td class="e">${"%s &euro;" % formatLang(invs.total_power)}</td></tr>
    % if invs.has_exces_potencia:
        <tr><td>${_(u"Excés de potència")}</td><td class="e">${"%s &euro;" % formatLang(invs.total_exces_consumida)}</td></tr>
    % endif
    % if invs.total_ractive > 0:
        <tr><td>${_(u"Penalització per energia reactiva")}</td><td class="e">${"%s &euro;" % formatLang(invs.total_ractive)}</td></tr>
    % endif
        <tr><td>${_(u"Impost d'electricitat")}</td><td class="e">${"%s &euro;" % formatLang(invs.iese)}</td></tr>
        <tr><td>${_(u"Lloguer del comptador")}</td><td class="e">${"%s &euro;" % formatLang(invs.total_rent)}</td></tr>
    % if (invs.total_altres + invs.total_bosocial) != 0:
        <tr><td>${_(u"Altres conceptes")}</td><td class="e">${"%s &euro;" % formatLang(invs.total_altres + invs.total_bosocial)}</td></tr>
    % endif
    % for n, v in invs.impostos.items():
        <tr><td>${n}</td><td class="e">${"%s &euro;" % formatLang(v)}</td></tr>
    % endfor
    % if invs.donatiu > 0:
        <tr><td>${_(u"Donatiu voluntari (0,01 &euro;/kWh) (exempt d'IVA)")}</td><td class="e">${"%s &euro;" % formatLang(invs.donatiu)}</td></tr>
    % endif
        <tr class="total"><td>${_(u"TOTAL IMPORT FACTURA")}</td><td class="e">${"%s &euro;" % formatLang(invs.total_amount)}</td></tr>
        </table>
    </div>
