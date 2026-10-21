<%page args="mail_data"/>
<% data = mail_data %>
% if data['lang'] == 'ca_ES':
<p>Pots consultar en qualsevol moment <a target="_blank" href="https://www.somenergia.coop/ca/tarifes-llum/domestic-periodes">totes les tarifes</a> i l'<a target="_blank" href="https://www.somenergia.coop/ca/historic-tarifa-periodes">històric de tarifes</a>.</p>
<h3 style="font-size: 16px">Informació legal</h3>
% if data['mode_facturacio'] == 'atr':
<p class="p-legal">La <a target="_blank" href="https://back.somenergia.coop/storage/app/media/DOCS/legal/ca/CCGG/Condicions-Generals-contracte-subministrament-energia-electrica-SomEnergia.pdf">clàusula contractual de les Condicions Generals</a> que ens autoritza a fer aquest canvi de preus de les tarifes períodes és la clàusula 3.3.</p>
% else:
<p class="p-legal">La <a target="_blank" href="https://back.somenergia.coop/storage/app/media/DOCS/Condicions-Generals-contracte-subministrament-energia-electrica-SomEnergia.pdf">clàusula contractual de les Condicions Generals</a> que ens autoritza a fer aquest canvi de preus de les tarifes indexades és la clàusula 5.3 (ii).</p>
% endif
<p class="p-legal">Pots accedir al comparador d'ofertes que elabora la Comissió Nacional dels Mercats i la Competència (CNMC) a través <a target="_blank" href="https://comparador.cnmc.gob.es/">d'aquest enllaç</a>. El comparador permet consultar i comparar les diferents ofertes vigents d'algunes de les comercialitzadores del mercat lliure. Tingues en compte que les tarifes de Som Energia no hi estan incloses.</p>
<p class="p-legal">
% if data['modcon']:
Hem
% else:
T’adjuntem en aquest correu el teu contracte actualitzat amb els nous preus. Si hi estàs d’acord, <strong>no cal que ens retornis el document signat</strong>, ja que l'actualització dels preus de les nostres tarifes s'aplica automàticament. Igualment, hem
% endif
 d’informar-te que si, per alguna raó, aquest canvi de preus et fes replantejar seguir amb aquesta tarifa, podries canviar-te de tarifa (<a target="_blank" href="https://ca.support.somenergia.coop/article/1344-modificacio-de-la-tarifa-de-periodes-a-indexada-i-dindexada-a-periodes">a través de la teva Oficina Virtual</a>), o podries donar de baixa el teu contracte amb nosaltres, bé comunicant-nos-ho directament enviant-nos una còpia del <a target="_blank" href="https://back.somenergia.coop/storage/app/media/DOCS/Desistiment_Plantilla_CAT.pdf">document de desistiment</a>, o bé mitjançant un canvi de comercialitzadora. Et recordem que a la cooperativa no apliquem penalitzacions ni clàusules de permanència en cap moment. Així doncs, si decidissis marxar, només et facturaríem el consum realitzat fins al dia en què deixem de subministrar-te energia, amb els preus vigents a cada moment.</p>
% else:
<p>Puedes consultar en cualquier momento <a target="_blank" href="https://www.somenergia.coop/es/tarifas-luz/domestico-periodos/">todas las tarifas</a> y el <a target="_blank" href="https://www.somenergia.coop/es/historico-tarifa-periodos">histórico de tarifas</a>.</p>
<h3 style="font-size: 16px">Información legal</h3>
% if data['mode_facturacio'] == 'atr':
<p class="p-legal">La <a target="_blank" href="https://back.somenergia.coop/storage/app/media/DOCS/legal/es/CCGG/Condiciones-Generales-contrato-suministro-energia-electrica-SomEnergia.pdf">cláusula contractual de las Condiciones Generales</a> que nos autoriza a realizar este cambio de precios de las tarifas periodos es la cláusula 3.3.</p>
% else:
<p class="p-legal">La <a target="_blank" href="https://back-nova-test.somenergia.coop/storage/app/media/DOCS/Condiciones-generales-contrato-suministro-energia-electrica-SomEnergia.pdf">cláusula contractual de las Condiciones Generales</a> que nos autoriza a realizar este cambio de precios de las tarifas indexadas es la cláusula 5.3 (ii).</p>
% endif
<p class="p-legal">Puedes acceder al comparador de ofertas que elabora la Comisión Nacional de los Mercados y la Competencia (CNMC) a través de <a target="_blank" href="https://comparador.cnmc.gob.es/">este enlace</a>. El comparador permite consultar y comparar las distintas ofertas vigentes de algunas de las comercializadoras del mercado libre. Ten en cuenta que las tarifas de Som Energia no están incluidas.</p>
<p class="p-legal">
% if data['modcon']:
Debemos
% else:
Te adjuntamos en este correo tu contrato actualizado con los nuevos precios. Si estás de acuerdo, <strong>no es necesario que nos devuelvas el documento firmado</strong>, puesto que la actualización de los precios de nuestras tarifas se aplica automáticamente. Igualmente, debemos
% endif
 informarte de que si, por alguna razón, este cambio de precios te hiciese replantear seguir con esta tarifa, podrías cambiarte de tarifa (<a target="_blank" href="https://es.support.somenergia.coop/article/1345-modificacion-de-la-tarifa-de-periodos-a-indexada-y-de-indexada-a-periodos">a través de tu Oficina Virtual</a>), o podrías dar de baja tu contrato con nosotros, bien comunicándolo directamente enviándonos una copia del <a target="_blank" href="https://back-nova-test.somenergia.coop/storage/app/media/DOCS/Desistimiento_Plantilla_CAST.pdf">documento de desistimiento</a>, o bien mediante un cambio de comercializadora. Te recordamos que en la cooperativa no aplicamos penalizaciones ni cláusulas de permanencia en ningún momento. Así pues, si decidieras marcharte, sólo te facturaríamos el consumo realizado hasta el día en que dejamos de suministrarte energía, con los precios vigentes en cada momento.</p>
% endif
