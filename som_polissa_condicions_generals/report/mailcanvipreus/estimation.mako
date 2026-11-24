<%page args="mail_data"/>
<% data = mail_data %>
<%
    ca = data['lang'] == 'ca_ES'
    def text(catalan, spanish):
        value = catalan if ca else spanish
        return value.decode('utf-8') if isinstance(value, bytes) else value
%>
<h1>${text('Estimació', 'Estimación')}</h1>
% if ca:
% if data['origen'] in ['pdf', 'consums_periods']:
<p>Tal com estableix la normativa, hem fet <strong>una estimació de caràcter orientatiu</strong> del que et costaria l'energia i la potència durant un any, si apliquéssim els preus actuals i si apliquéssim els preus nous. L'estimació l'hem fet a partir de les dades que tenim respecte al que has consumit de la xarxa elèctrica durant els últims 12 mesos (aproximadament ${data['consum_total']} kWh) i les potències que tens contractades, i no inclou el lloguer de comptador ni els costos dels Serveis d'Ajust.</p>
% elif data['origen'] == 'cnmc':
<p>Tal com estableix la normativa, hem fet una <strong>estimació de caràcter orientatiu</strong> del que et costaria l'energia i la potència durant un any, aplicant-hi els preus actuals i els preus nous. L'estimació l'hem fet a partir de les dades que tenim dels teus consums anteriors (sense tenir en compte ni el lloguer de comptador, ni els costos dels Serveis d'Ajust), extrapolant-les segons el consum mitjà que sol haver-hi a cada mes (segons dades de la Comissió Nacional dels Mercats i la Competència). Amb això n'hem obtingut un consum anual, que és el que fem servir per a la comparació.</p>
% elif data['origen'] == 'estadistic':
<p>Tal com estableix la normativa, hem fet una <strong>estimació de caràcter orientatiu</strong> del que et costaria l'energia i la potència durant un any, aplicant-hi els preus actuals i els preus nous. L'estimació l'hem fet en funció de la potència contractada més alta que tens (${data['potencia']} kW), l'ús d'electricitat que sol haver-hi amb aquesta potència i agafant de referència un contracte estàndard, sense el lloguer de comptador ni els Serveis d'Ajust.</p>
% elif data['origen'] == 'indexada':
<p>Estimació orientativa del cost anual amb la tarifa indexada, calculada amb el consum anual disponible i els consums tipus del backend. El resultat no prediu els preus futurs del mercat.</p>
% else:
<% raise ValueError('Unsupported estimation source') %>
% endif
% else:
% if data['origen'] in ['pdf', 'consums_periods']:
<p>Tal y como establece la normativa, hemos hecho una <strong>estimación de carácter orientativo</strong> de lo que te costaría la energía y la potencia durante un año, si aplicáramos los precios actuales y si aplicáramos los nuevos. La estimación la hemos hecho a partir de los datos que tenemos respecto a lo consumido de la red eléctrica durante los últimos 12 meses (aproximadamente ${data['consum_total']} kWh) y las potencias que tienes contratadas, y no incluye ni el alquiler del contador ni los Servicios de Ajuste.</p>
% elif data['origen'] == 'cnmc':
<p>Tal y como establece la normativa, hemos hecho una <strong>estimación de carácter orientativo</strong> de lo que te costaría la energía y la potencia durante un año, aplicando los precios actuales y los nuevos. La estimación la hemos hecho a partir de los datos que tenemos de tus consumos anteriores (sin tener en cuenta ni el alquiler de contador, ni los Servicios de Ajuste), extrapolándolos según el consumo medio que suele haber a cada mes (según datos de la Comisión Nacional de los Mercados y la Competencia). Con esto hemos obtenido un consumo anual, que es el que utilizamos para la comparación.</p>
% elif data['origen'] == 'estadistic':
<p>Tal y como establece la normativa, hemos hecho una <strong>estimación de carácter orientativo</strong> de lo que te costaría la energía y la potencia durante un año, aplicando los precios actuales y los nuevos. La estimación la hemos hecho en función de la potencia contratada más alta que tienes (${data['potencia']} kW), el uso de electricidad que suele haber con esta potencia y cogiendo de referencia un contrato estándar, sin el alquiler de contador ni los Servicios de Ajuste.</p>
% elif data['origen'] == 'indexada':
<p>Estimación orientativa del coste anual con la tarifa indexada, calculada con el consumo anual disponible y los consumos tipo del backend. El resultado no predice los precios futuros del mercado.</p>
% else:
<% raise ValueError('Unsupported estimation source') %>
% endif
% endif
<p>${text("L'estimació la pots veure sense impostos i amb impostos inclosos", 'La estimación la puedes ver sin impuestos y con impuestos incluidos')}
(${data['impostos_str'] | h} ${text("i l'impost elèctric del", 'y el impuesto eléctrico del')} ${data['impost_electric_str'] | h}).</p>
<h3>${text('Cost anual estimat, en euros/any, del subministrament (energia i potència)', 'Coste anual estimado, en euros/año, del suministro (energía y potencia)')}</h3>
<table class="purchase_content" width="100%" cellpadding="8" cellspacing="0" role="presentation">
<tr><th>${text('Impostos', 'Impuestos')}</th><th>${text('Cost estimat amb els preus actuals', 'Coste estimado con los precios actuales')}</th><th>${text('Cost estimat amb els nous preus', 'Coste estimado con los nuevos precios')}</th></tr>
% for suffix, label in [('', text('Sense impostos', 'Sin impuestos')), ('_imp', text('Amb impostos', 'Con impuestos'))]:
<tr><td>${label}</td><td>${data['preu_vell' + suffix]}</td><td>${data['preu_nou' + suffix]}</td></tr>
% endfor
</table>
% if data['te_gkwh']:
<h3>Generation kWh</h3>
% if data['gkwh_estimation']['origen'] == 'no_data':
<p>${text('No hi ha dades suficients per estimar el cost anual de Generation kWh.', 'No hay datos suficientes para estimar el coste anual de Generation kWh.')}</p>
% else:
<p>${text('Consum anual estimat', 'Consumo anual estimado')}: ${data['gkwh_estimation']['consum_total']} kWh.
${text('Origen', 'Origen')}: ${data['gkwh_estimation']['origen'] | h}.</p>
<table class="purchase_content" width="100%" cellpadding="8" cellspacing="0" role="presentation">
<tr><th>${text('Impostos', 'Impuestos')}</th><th>${text('Cost estimat amb els preus actuals', 'Coste estimado con los precios actuales')}</th><th>${text('Cost estimat amb els nous preus', 'Coste estimado con los nuevos precios')}</th></tr>
% for suffix, label in [('', text('Sense impostos', 'Sin impuestos')), ('_imp', text('Amb impostos', 'Con impuestos'))]:
<tr><td>${label}</td><td>${data['gkwh_estimation']['preu_vell' + suffix]}</td><td>${data['gkwh_estimation']['preu_nou' + suffix]}</td></tr>
% endfor
</table>
% endif
% endif
% if ca:
<p>Tingues en compte que això són estimacions aproximades, i que els imports finals <strong>dependran de circumstàncies</strong> que no podem preveure, com per exemple els horaris i l'ús d'energia que finalment facis, altres variacions de preus durant l'any, o canvis que hi pugui haver al mercat elèctric o en el context geopolític.</p>
% else:
<p>Ten en cuenta que esto son estimaciones aproximadas, y que los importes finales <strong>dependerán de circunstancias</strong> que no podemos prever, como por ejemplo los horarios y el uso de energía que finalmente hagas, otras variaciones de precios durante el año, o cambios que puedan producirse en el mercado eléctrico o en el contexto geopolítico.</p>
% endif
