# Verificació del canvi de preus

## Resultats

S'han fet les proves amb PostgreSQL, MongoDB i Redis iniciats, Python 2.7 de
l'entorn `erp` i `scripts/run-tests-worktree.sh`, declarant explícitament els dos
addons afectats. La sincronització de dependències s'ha omès amb autorització
expressa; no s'ha modificat GISCE ERP.

### Proves específiques

- 30 tests ERP nous: campanya, seguretat, selecció, dates, reenviaments, càlculs,
  decimals, adjunts, Poweremail i migració.
- PDF real amb Puppeteer 22.15.0 i Chromium local: l'HTML és exactament el de
  Poweremail; el PDF generat conté la data, el text editorial i CNMC.
- `som_indexada`: 17 de 18 tests passen. L'única fallada és el catàleg de
  traduccions absent del mòdul, que també falla amb el codi base.
- Oomako: deu casos sintètics registrats; comparació B2B local i assertions
  independents de números, dates, estructura, llengua i contingut legal.
- Les dues proves d'assertions de renderització passen amb Python 2.7 i Python 3.
- Compilació de sintaxi amb Python 2.7 i Python 3 dels fitxers Python nous o
  modificats compatibles amb ambdós entorns. El CLI històric `oomako` continua
  requerint Python 2; les incorporacions de renderització es proven també amb 3.
- Flake8 dels fitxers Python del canvi, sense errors.

Els càlculs es proven amb entrades deterministes i fórmules esperades: energia,
potència, bo social, ajustos de Generation kWh, impostos, arrodoniments i
coeficients indexats. Les rutes de decimals coincideixen amb les històriques.
Es conserven els valors per defecte dels cridadors antics; les dates i el mapa
fiscal explícits són paràmetres del nou circuit optatiu. No es presenta la
comparació com una auditoria de totes les tarifes reals de producció.

### Suite completa i comparació amb la base

S'ha exportat amb `git archive` el codi immutable de la base `457eef5d`, sense
crear una branca ni editar la còpia. La base i el canvi s'han executat en bases
de dades noves i diferents, amb les mateixes dependències compartides i el
mateix wrapper segur. També es declaren els addons de la còpia exportada:
no s'han canviat symlinks manualment.

| Suite | Base sense aquest canvi | Implementació |
| --- | --- | --- |
| `som_indexada` | 18 tests; 1 fallada de catàleg absent | 18 tests; la mateixa fallada |
| `som_polissa_condicions_generals` | 63 tests; 5 fallades, 16 errors, 2 omesos | 93 tests; 4 fallades, 16 errors, 2 omesos |

**No hi ha cap test fallit nou respecte de la base.** Els 30 tests incorporats
passen. La fallada d'accés al backend PDF present a la base queda resolta amb
el permís de lectura explícit d'aquest canvi.

La suite global **no està verda**. Els 20 casos encara fallits de condicions
generals i el cas de traduccions de `som_indexada` també fallen sense aquest
canvi: serveis/rutes dels reports contractuals, expectatives de migracions
anteriors, dades demo de CUPS, una condició de secció de Generation kWh/GURB,
cadenes anteriors absents al POT i el catàleg absent de `som_indexada`.
No s'han arreglat, omès ni relaxat per ocultar-los, ni s'ha modificat GISCE ERP
per fer-los passar.

Una execució inicial en una DB reutilitzada tenia a més un error per una
referència fiscal demo amb ID literal 1 absent. La comparació anterior utilitza
DBs noves per evitar atribuir aquest estat local a la implementació.

Logs locals de l'execució (temporals, no dades de producció):

- `/tmp/price-change-destral-baseline.log`: codi base, DB nova.
- `/tmp/price-change-destral-verified.log`: implementació, DB nova.
- `/tmp/price-change-destral-final.log`: selecció específica dels tests nous.
- `/tmp/price-change-indexed-final.log`: 17 casos passen i reapareix únicament
  el catàleg de traduccions absent que ja falla a la base.
- `/tmp/price-change-oomako.log`: B2B sintètic.

## Matriu de cobertura

| Requisit | Evidència |
| --- | --- |
| Català i castellà | Casos Mako de totes dues llengües; exigència de traduccions explícites de tots els banners requerits |
| 2.0TD i altres tarifes | Casos 2.0TD, 3.0TD i 6.1TD; dominis sobre `polissa_id` i predicats de pòlissa/enviament provats |
| Vigència | Inclusió del dia inicial/final i rebuig fora de límit |
| Absències i ambigüitats | Banners absents, prioritats que no amaguen duplicats, traducció castellana absent i traduccions duplicades |
| Aïllament | Selecció per plantilla; una còpia sense dominis propis falla, no envia un cos buit |
| Dates compartides | Contextos antics/nous capturats en càlculs i delegació; assumpte, HTML i PDF mostren la mateixa entrada en vigor |
| Reenviaments | Després de fixar contingut, canviar dates del lot o eliminar banners no canvia el snapshot; canvi de plantilla rebutjat |
| Còpia segura | No conserva snapshot, correu associat, estat enviat ni data d'enviament |
| Modificació pendent | Alerta abans de la salutació i text legal que no anuncia el contracte adjunt en aquest cas |
| Autoconsum | Condició existent de compensació/períodes; combinacions amb/sense compensació i amb indexada |
| Generation kWh | Taules, imports, ajustos i cas sense dades d'estimació |
| Fiscalitat | IVA, IVA reduït i IGIC en fórmules; mapa fiscal explícit per a indexada; textos d'impostos provinents del backend |
| Orígens de consum | `pdf`, `consums_periods`, `cnmc`, `estadistic`, `indexada`; origen desconegut bloquejat en Mako |
| Pujades i baixades | Comparatives numèriques sense afirmar que el preu no ha canviat; valors independents per període |
| Contingut contractual | Clàusula segons modalitat/font històrica, CNMC, opcions de canvi/baixa i absència de permanència |
| Adjunts | Un únic PDF en l'enviament quan el text anuncia el contracte; absència i tipus incorrecte bloquejats |
| Poweremail | Renderer real, assumpte dinàmic i CC/BCC inicialment buits; propagació d'errors obligatòria |
| PDF | Conversió real; HTML idèntic al de Poweremail; selecció no ambigua i verificació pòlissa/enviament |
| Permisos | Editor pot canviar HTML però no codis, prioritats, imatge, eliminació ni traduccions alienes |
| Codi executable | Rebuig de Mako, scripts, protocols executables, atributs actius i imatges; també per a traduccions d'administrador |
| Migració | Execució real dues vegades, camps inicialitzats i conservació de plantilles `noupdate` |
| Històric | Cap plantilla històrica modificada a oomakotest; no es reescriu `canviPreusBackend` |
| GISCE ERP | Diff versionat buit; únic fitxer no versionat observat, `docker-compose.yaml`, ja hi era abans del treball |

## Reproducció

Des del worktree d'addons, amb els serveis de tests en marxa:

```bash
PYENV_VERSION=erp scripts/run-tests-worktree.sh \
  --addon som_polissa_condicions_generals --addon som_indexada -- \
  --no-requirements -m som_polissa_condicions_generals \
  -t TestPriceChangeCampaign -t TestPriceChangeCalculations \
  -t TestPriceChangeValidation
```

Per incloure el smoke PDF real, cal el runtime que ja requereix el report
Puppeteer. En aquesta verificació s'ha instal·lat temporalment fora dels
repositoris, sense descarregar un navegador nou:

```bash
PUPPETEER_SKIP_DOWNLOAD=true npm install \
  --prefix /tmp/price-change-pdf-tooling --no-package-lock --ignore-scripts \
  puppeteer@22.15.0
export NODE_PATH=/tmp/price-change-pdf-tooling/node_modules
export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
export SOM_PRICE_CHANGE_PDF_SMOKE=1
```

Sense aquesta opció, el test de conversió real s'identifica explícitament com
omès; els tests de dates, contracte de renderització i contingut no se'n fan
passar per substituts.

A oomakotest, apuntant al worktree d'addons, sense connectar amb ERP ni SMTP:

```bash
export OPENERP_TEMPLATE_ADDONS_PATH=/ruta/al/worktree/openerp_som_addons
PYENV_VERSION=erp python -m unittest -v test_price_change_render
python3 -m unittest -v test_price_change_render
PYENV_VERSION=erp ./oomako test canviPreusReutilitzable
```

Els esperats B2B són locals i ignorats per Git, com la resta d'oomakotest.
En un checkout nou, cal revisar i establir els esperats; no s'ha d'acceptar
cegament un canvi posterior. Les assertions versionades no requereixen aquests
fitxers i validen les deu entrades de `testcases.yaml` independentment.
La nova entrada és sintètica: no té cap `poweremailId` de producció ni IDs reals
de clients. La plantilla real es prepara amb l'XML de l'addon, no amb l'upload
d'aquest cas sintètic.

## Pendent abans d'activació: verificacions humanes

No s'ha activat cap campanya ni s'ha enviat cap correu. Continuen pendents:

- revisió de negoci de segments, modalitats, dates i continguts bilingües;
- revisió jurídica de textos, terminis, clàusules i enllaços històrics;
- comprovació semàntica que el PDF adjunt és el contracte correcte;
- comprovació de destinataris reals, CC/BCC, permisos i estat del lot;
- proves en clients de correu representatius;
- validació de configuració i versions reals de producció.

Aquestes comprovacions no es declaren executades ni aprovades implícitament.
