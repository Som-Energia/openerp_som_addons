# Massive Importer - mòdul som_crawlers
Mòdul compatible amb PowerERP per descarregar fitxers de distribuidores elèctriques del sistema ibèric

## Models
### Tasca planificada: som.crawlers.task
Té hores i dies d’execució i un seguit de passes que s’han d’executar.

### Pas d’acció planificada: som.crawlers.task.step
Pas d'una tasca planificada

### Acció executada: som.crawlers.task.result
Conté el resultat de l’execució de a tasca determinada en una hora determinada.

### Configuració: som.crawlers.config
Conté la configuració d'una tasca

## API d'i-DE: configuració de l'accés

Els tres portals comparteixen el client i els endpoints, amb configuracions
separades de credencials:

| Distribuïdora | Codi `Portal` / `codPortal` | Configuració ERP |
| --- | --- | --- |
| Iberdrola | `0021` | `iberdrola_api_conf` |
| Conquense | `0032` | `conquense_api_conf` |
| Anselmo León | `0118` | `anselmo_api_conf` |

A cadascuna de les configuracions API, establiu:

- URL del portal: `https://www.i-de.es/pwelconq/services/arq/` (no `wwwd`).
- Usuari i contrasenya autoritzats per a la API.
- `API-Key`: clau facilitada per i-DE, introduïda manualment al formulari de
  configuració. El camp es mostra emmascarat; això no és xifratge en repòs.

El client envia `API-Key`, `User-Agent: portal_agentes` i `Portal` tant al
login com a les peticions posteriors. Conserva les cookies durant l'execució,
actualitza el JWT si el servidor en retorna un de nou i limita el temps
d'espera HTTP. No afegiu credencials ni tokens a exemples, dades XML o logs.

La migració `post-0006_ADD_ide_api_credentials.py` inicialitza el camp, recarrega
la vista i corregeix les URLs buides o antigues de les tres configuracions API.
Conserva URLs personalitzades i les credencials de cada configuració per separat,
i no activa cap tasca. No es copien credencials ni API-Keys entre portals.
L'API-Key no té valor per defecte: l'operador l'ha de configurar abans de les proves.

### Descàrrega síncrona

El client usa `DescargarMensajesMasivosAPI` amb `filtros.proceso`, respectant
l'interval i l'opció de només pendents configurats. El payload segueix la nova
col·lecció: `mensajesFirmados: false` i `marcados: false`, sense `loginUsuario`.
Aquest ajust del payload encara s'ha de contrastar amb una prova real a i-DE.

- HTTP 400 amb «No se han encontrado mensajes para descargar.» es tracta com a
  `NoResultsException`, igual que un ZIP buit o que només contingui directoris.
- HTTP 400 per superar els 1.000 missatges produeix un error específic i no es
  confon amb una resposta sense resultats. No es reintenta automàticament.
- HTTP 401/403 es tracta com a error d'accés; altres errors HTTP no s'oculten.
- No se segueixen redireccions automàticament, per no reenviar credencials
  cap a altres rutes o hosts.
- Es valida l'estructura i el CRC del ZIP abans de desar-lo; no es descodifica
  el binari com a text ni es descomprimeix al disc. El `Content-Type` no és
  suficient per considerar que la resposta és un ZIP vàlid.
- El desament és atòmic i usa un temporal privat fora del directori que llegeix
  l'importador. Una descàrrega invàlida o una fallada de publicació no substitueix
  un fitxer de destinació existent.

### Interval de dates

`get_intervals()` usa sempre la data i hora actuals, independentment del nom del
servidor. L'inici és aquest mateix instant menys `days_of_margin` dies. No
s'arrodoneix a mitjanit ni es força una data històrica fora de producció.
La correcció és compartida amb els downloaders CIDE; als tests el rellotge es
simula explícitament, sense condicionar el codi al hostname.

### Descàrrega F1 amb ticket als tres portals

Els downloaders `iberdrola_f1`, `conquense_f1` i `anselmo_f1` comparteixen el
flux següent. Cada classe conserva el seu codi de portal, la seva configuració
i el seu directori de sortida:

1. `API/gmagente/DescargaAbsoluta` crea el ticket. La resposta real validada és
   `{"codigoDescarga": "28282"}`; aquest camp és diferent de `codDescarga`.
2. `API/gmagente/ConsultarEstadoTicket`, amb `{"codDescarga": "28282"}`, retorna
   `estado: "P"` mentre està pendent i `estado: "F"` quan està preparat.
3. `ConsultaDescargaAPI`, **sense `API/gmagente`**, rep `codDescarga` i retorna
   el ZIP complet.
4. Es valida el ZIP i se'n genera un altre només amb fitxers `.xml` que
   contenen `F1` al nom, sense distingir majúscules/minúscules. No es comprova
   el contingut XML ni es considera el nom de les carpetes per seleccionar-los.
5. El ZIP filtrat es desa al camí habitual perquè el pas existent l'adjunti i
   l'importi. El ZIP complet no s'escriu al disc ni es passa a l'importador.

Es conserva exactament l'interval retornat per `get_intervals()`, separat en
camps de data i hora. `pending_files_only` determina `Pendientes Descargar` o
`Todos`; `firmado` i `marcarDescargados` s'envien a `false`. El camp `filtro`
s'envia buit per compatibilitat: i-DE ha confirmat que no té funcionalitat.

La consulta d'estat es fa immediatament i després espera 60 segons entre
peticions, amb un pressupost de 30 minuts i un límit de seguretat de 31
consultes. Cada consulta HTTP queda
limitada al mínim entre el timeout habitual i el pressupost restant. Aquests
límits no inclouen la creació del ticket ni la descàrrega final, que tenen
cadascuna el seu timeout HTTP. No s'interpreten estats desconeguts com a èxit
ni com a absència de resultats.

El codi del ticket i els recomptes de fitxers es registren sense XML ni
credencials. En cas de fallada, el mateix objecte pot reutilitzar el ticket;
**no es persisteix entre execucions ERP**, segons el criteri acordat. Si
s'esgota l'espera, l'error inclou el codi del ticket i indica que l'equip el pot
consultar i descarregar manualment quan estigui preparat. Una nova execució
crea un altre objecte: abans de reintentar després d'un timeout, consulteu el
ticket dels logs per evitar generar descàrregues duplicades. La creació no es
reintenta automàticament si falla abans de rebre el codi.

Si el ZIP és buit o no conté cap XML F1, es retorna `NoResultsException` i
no es genera cap ZIP nou. La tasca existent s'atura abans del pas d'importació.
Un error de descàrrega o filtratge no substitueix un fitxer anterior.

La resta de processos dels tres portals conserven el camí síncron amb filtre
de procés. Q1 continua sent només descàrrega, sense importació.

El flux real observat a i-DE correspon a Iberdrola (`0021`). La implementació
per a Conquense i Anselmo està coberta amb tests HTTP simulats del login, les
capçaleres, el ticket i el ZIP filtrat; cal confirmar amb l'API real els permisos
i el comportament de cadascun dels altres portals abans de donar-los per validats.

### Criteris operatius acordats

- Es manté l'activació automàtica de les tasques API prevista a la PR original.
- La deduplicació de factures continua a càrrec de l'importador ERP existent;
  no s'afegeix cap mecanisme de deduplicació en aquest canvi.
- Si el ticket no està preparat al cap de 30 minuts, l'equip corresponent el
  recuperarà manualment. No s'afegeix persistència del ticket entre jobs.

### Integració pendent abans de producció

- Fer la prova real des de l'ERP de la descàrrega i la importació F1 als tres portals.
- Contrastar el payload síncron actualitzat amb crides reals a cada portal.
