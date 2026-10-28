# Review de la PR 1508

## Decisions aplicades

- **POT:** restaurat exactament a la base de la PR (`457eef5d`), no al fitxer
  modificat per la primera implementació. El seu blob és
  `089a1fb8dfd0ad4a43c04bac0f1d1638f3459dad`.
- **Poweremail:** retirada l'herència de `poweremail.templates`. No s'intercepta
  `get_mailbox_values()` ni es força un tractament nou dels errors.
- **Lots:** retirada l'herència de `som.infoenergia.lot.enviament` i els seus
  tres camps de dates. Els banners es seleccionen amb la data actual.
- **Enviaments:** retirada l'herència de `som.enviament.massiu`. No hi ha
  snapshot, bloqueig de fila, escriptures durant la renderització ni
  sobreescriptures de `create/write/copy`.
- **Banners:** retirada l'herència de `report.banner`, el grup editorial,
  les ACL/vistes especials i les validacions globals d'HTML. Es reutilitza
  `get_report_banners()` amb les prioritats, dominis, vigències, traduccions i
  permisos que ja ofereix l'eina.
- **Traduccions:** es manté retirada l'herència d'`ir.translation`. No hi ha
  restriccions noves sobre operacions habituals de traducció.

No se substitueixen aquestes herències per un altre gestor de campanyes ni
per models auxiliars. `models/price_change_campaign.py`, el seu import i els
helpers de validació descartats s'eliminen; la migració deixa d'inicialitzar
els models compartits i de carregar les vistes descartades.

El backend específic del correu només prepara les dades, resol els preus nous,
consulta els banners i informa de l'absència d'un bloc necessari. El contingut
editorial no es compila com a Mako. Poweremail continua decidint com tracta
els errors segons el seu comportament i context habituals.

La data de selecció i dels preus actuals és la del dia d'execució. La data
futura dels preus nous es resol amb la llista de preus existent; no és una data
nova configurable al lot. Els reenviaments consulten el contingut vigent i
no prometen reproduir una versió anterior.

## Canvi fiscal acceptat

`som_indexada/utils.py` accepta opcionalment el mapa fiscal del backend per no
aplicar sempre IE 5,11% i IVA 21% a l'estimació indexada. Fora d'aquest circuit
manté els valors històrics. No és una auditoria fiscal general.

## Mako: encara pendent

La ubicació dels Mako continua pendent de discussió. No s'ha donat per aprovat
cap trasllat en aquesta review.

`somenergia-oomakotest` ja és font de plantilles pujades a producció, però
`oomako upload` puja el cos de la plantilla i no publica els fitxers locals
referenciats per `include`. Actualment escriu `def_body_text`, mentre que el
PDF llegeix `def_body_html`. La fixture sintètica de la PR 237 no té
`poweremailId` de producció.

Per moure els Mako cal definir una font única autocontinguda o un empaquetat
explícit i una publicació coherent del cos per correu/PDF. No n'hi ha prou amb
moure els cinc fitxers, ni s'ha d'afegir una dependència del checkout de tests
al servidor o mantenir dues còpies divergents.
