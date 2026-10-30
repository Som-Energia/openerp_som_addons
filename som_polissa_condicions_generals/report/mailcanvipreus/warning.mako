<%page args="mail_data"/>
<% data = mail_data %>
% if data['modcon']:
<div style="background-color: #D3E5C3; border: 4px solid #657557; padding: 1em;">
% if data['lang'] == 'ca_ES':
<p>Som conscients que el teu contracte està pendent d'un canvi de tarifa cap a la
<strong>tarifa ${data['tarifa_acces'] | h} ${data['modcon'] | h}</strong>, que s'hauria de produir en les pròximes setmanes.
Igualment, t'expliquem els canvis de preu que aplicarem a partir de
${data['campaign']['effective_date'] | h}, i que t'afectaran si, per algun motiu,
el teu contracte segueix amb la tarifa actual.</p>
% else:
<p>Somos conscientes de que tu contrato está pendiente de un cambio de tarifa hacia la
<strong>tarifa ${data['tarifa_acces'] | h} ${data['modcon'] | h}</strong>, que debería producirse en las próximas semanas.
Igualmente, te explicamos los cambios de precio que aplicaremos a partir de
${data['campaign']['effective_date'] | h}, y que te afectarán si, por algún motivo,
tu contrato sigue con la tarifa actual.</p>
% endif
</div>
% endif
