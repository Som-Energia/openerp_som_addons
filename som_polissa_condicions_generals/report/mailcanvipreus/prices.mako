<%page args="mail_data"/>
<% data = mail_data %>
<%
    ca = data['lang'] == 'ca_ES'
    def text(catalan, spanish):
        value = catalan if ca else spanish
        return value.decode('utf-8') if isinstance(value, bytes) else value
%>
<h1>${text('Nous preus i comparativa amb preus actuals', 'Nuevos precios y comparativa con precios actuales')}</h1>
<p>${text('Data dels preus actuals', 'Fecha de los precios actuales')}:
${data['campaign']['old_price_date'] | h}.
${text('Nous preus vigents a partir de', 'Nuevos precios vigentes a partir de')}
${data['campaign']['effective_date'] | h}.</p>
<p>${text('Tarifa', 'Tarifa')} ${data['tarifa_acces'] | h} (${data['mode_facturacio'] | h}).
${text('Impostos aplicats', 'Impuestos aplicados')}: ${data['impostos_str'] | h}
${text("i l'impost elèctric del", 'y el impuesto eléctrico del')} ${data['impost_electric_str'] | h}.</p>
% for term, unit, title_ca, title_es in [('te', 'euros/kWh', "Preu del terme d'energia", 'Precio del término de energía'), ('tp', 'euros/kW/any', 'Preu de la potència', 'Precio de la potencia')]:
% if term == 'tp' or data['mode_facturacio'] == 'atr':
<h3>${text(title_ca, title_es)} (${unit})</h3>
<table class="purchase_content" width="100%" cellpadding="8" cellspacing="0" role="presentation">
<tr><th>${text('Període', 'Periodo')}</th><th>${text('Impostos', 'Impuestos')}</th><th>${text('Preus actuals', 'Precios actuales')}</th><th>${text('Preus nous', 'Precios nuevos')}</th></tr>
% for suffix, label in [('', text('Sense impostos', 'Sin impuestos')), ('_imp', text('Amb impostos', 'Con impuestos'))]:
% for period in sorted(data['preus_antics' + suffix][term]):
<tr><td>${period | h}</td><td>${label}</td><td>${data['preus_antics' + suffix][term][period]}</td><td>${data['preus_nous' + suffix][term][period]}</td></tr>
% endfor
% endfor
</table>
% endif
% endfor
% if data['mode_facturacio'] == 'index':
<h3>${text('Factor de gestió de la tarifa indexada', 'Factor de gestión de la tarifa indexada')} (euros/MWh)</h3>
<table class="purchase_content" width="100%" cellpadding="8" cellspacing="0" role="presentation">
<tr><th>${text('Preus actuals', 'Precios actuales')}</th><th>${text('Preus nous', 'Precios nuevos')}</th></tr>
<tr><td>${data['dades_index']['f_antiga']}</td><td>${data['dades_index']['f_nova']}</td></tr>
</table>
% endif
% if data['autoconsum']['compensacio'] and data['mode_facturacio'] == 'atr':
<h3>${text('Compensació dels excedents', 'Compensación de los excedentes')} (euros/kWh)</h3>
<table class="purchase_content" width="100%" cellpadding="8" cellspacing="0" role="presentation">
<tr><th>${text('Impostos', 'Impuestos')}</th><th>${text('Preus actuals', 'Precios actuales')}</th><th>${text('Preus nous', 'Precios nuevos')}</th></tr>
% for suffix, label in [('', text('Sense impostos', 'Sin impuestos')), ('_imp', text('Amb impostos', 'Con impuestos'))]:
<tr><td>${label}</td><td>${data['preu_auto_antic' + suffix]}</td><td>${data['preu_auto_nou' + suffix]}</td></tr>
% endfor
</table>
% endif
% if data['te_gkwh']:
<h3>Generation kWh (euros/kWh)</h3>
<table class="purchase_content" width="100%" cellpadding="8" cellspacing="0" role="presentation">
<tr><th>${text('Període', 'Periodo')}</th><th>${text('Impostos', 'Impuestos')}</th><th>${text('Preus actuals', 'Precios actuales')}</th><th>${text('Preus nous', 'Precios nuevos')}</th></tr>
% for suffix, label in [('', text('Sense impostos', 'Sin impuestos')), ('_imp', text('Amb impostos', 'Con impuestos'))]:
% for period in sorted(data['preus_antics_generation' + suffix]):
<tr><td>${period | h}</td><td>${label}</td><td>${data['preus_antics_generation' + suffix][period]}</td><td>${data['preus_nous_generation' + suffix][period]}</td></tr>
% endfor
% endfor
</table>
% endif
