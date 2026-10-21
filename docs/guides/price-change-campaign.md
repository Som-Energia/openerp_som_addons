# Correu reutilitzable de canvi de preus

## Abast i contracte

La plantilla `som_polissa_condicions_generals.price_change_campaign_template`
separa els textos editorials dels càlculs i dels components contractuals.
És una plantilla nova i optativa: no substitueix les històriques, no s'assigna
a lots existents i no activa cap enviament automàtic.

La configuració pertany al lot `som.infoenergia.lot.enviament`:

| Camp | Ús |
| --- | --- |
| `email_template` | Plantilla Poweremail i aïllament dels dominis |
| `price_change_selection_date` | Data de selecció de vigència dels banners |
| `price_change_old_price_date` | Data dels preus anteriors |
| `price_change_effective_date` | Entrada en vigor; preus nous, assumpte i text |

Les dates són explícites, en format `YYYY-MM-DD`. Els preus anteriors han de
precedir l'entrada en vigor; la selecció no pot ser posterior a l'entrada en
vigor. No hi ha periodicitat automàtica ni validació jurídica del termini.

El backend selecciona sobre **l'enviament massiu**, amb dominis sobre la seva
`polissa_id`; només després delega els càlculs al backend de pòlissa. El context
inclou `pem_template_id`. No s'intercanvien identificadors dels dos models.
L'idioma és el del titular: català i castellà, sense fallback silenciós.

## Continguts editorials

| Codi | Obligatorietat | Domini preparat |
| --- | --- | --- |
| `CANVI_PREUS_MOTIU` | Sempre | Una variant 2.0TD i una per a la resta |
| `CANVI_PREUS_AUTOCONSUM` | Compensació simplificada i modalitat `atr` | Subtipus 21 i períodes |
| `CANVI_PREUS_COMIAT` | Sempre | Tots els contractes |

2.0TD / resta conserva la segmentació existent: no defineix comercialment
què és domèstic o industrial. Es conserva també la condició existent del bloc
d'autoconsum; no s'estén automàticament a altres modalitats.

Es creen quatre esborranys buits, amb vigència **2099-01-01 a 2099-01-01**.
Aquesta data és una protecció d'esborrany, no una campanya real. L'equip tècnic
ha de preparar les vigències abans d'utilitzar-los. Encara que algú seleccioni
aquella data, els textos i les traduccions buits bloquegen la renderització.
Els esborranys i els dominis tenen XML IDs independents i `noupdate=1`.

El grup **Canvi de preus: edició de textos** dona accés a les entrades catalana
i castellana del menú d'enviaments massius. Les pantalles mostren codi i dates
com a informació de només lectura. El servidor restringeix l'edició a HTML i
traduccions d'aquests codis, també davant crides directes a l'ORM. No concedeix
creació, eliminació ni edició de codis, dominis, dates o prioritats.
No cal afegir el grup Banner Manager al personal editorial.

S'admet HTML senzill: paràgrafs, salts, èmfasi, llistes, títols i enllaços
HTTP/HTTPS/mailto. No s'admeten imatges, scripts, atributs d'esdeveniment,
CSS, iframes ni expressions/directives Mako. No és un editor visual.
El contingut editorial **no es compila com a Mako**.

Cal disposar de les dues llengües actives i de traduccions explícites
`report.banner,html` per a **ca_ES i es_ES**. El text font no substitueix una
traducció absent. També es rebutgen traduccions duplicades i tots els banners
aplicables superposats: la prioritat no amaga una configuració ambigua.

## Preparació d'una campanya

1. Revisar segments, modalitats, dates i textos amb negoci i assessorament jurídic.
2. Preparar els banners i la vigència real des del rol tècnic. Per a campanyes
   successives, conservar els banners històrics i crear-ne de nous amb vigències
   no superposades; no canviar els textos d'una campanya encara pendent de fixar.
3. Negoci edita només HTML i traduccions des dels dos menús editorials.
4. Crear un lot amb la plantilla reutilitzable i les tres dates. Configurar el
   compte remitent apropiat: no s'imposa cap compte de producció des de l'XML.
5. Generar i adjuntar els contractes amb el circuit existent. Si el text diu
   que s'adjunta el contracte, s'exigeix un únic adjunt a l'enviament, amb nom
   `.pdf` i capçalera PDF. Això coincideix amb el circuit massiu que adjunta el
   primer document de l'enviament. No certifica que el PDF contingui el contracte
   jurídicament correcte: cal revisar-ne el contingut i la data. El cas `modcon`
   manté el text existent que no anuncia aquest adjunt.
6. Renderitzar en un entorn controlat i validar tots els casos aplicables abans
   d'autoritzar un enviament. No és un flux d'aprovació ni un gestor de campanyes.
7. Revisar explícitament To, CC, BCC, adjunts i estat del lot abans d'activar-lo.
   Es conserven els destinataris titular/notificació de la referència; la
   configuració inicial no afegeix CC ni BCC. Els tests no envien correus.

Els controls s'apliquen per enviament en la renderització. El hook local de
Poweremail força la propagació dels errors per a aquesta plantilla i per a
còpies que utilitzin el mateix component: no es converteixen en un cos o
assumpte buit. No s'ha modificat el comportament de les altres plantilles.
No es declara una validació atòmica de tot el lot abans del primer enviament.

## Reenviaments i traçabilitat

`som.enviament.massiu.price_change_snapshot` conserva dates, plantilla, llengua
i els continguts editorials bilingües seleccionats. Es fixa en la **primera
renderització**, incloent-hi l'assumpte i la previsualització PDF. La selecció es
serialitza amb un bloqueig de la fila de l'enviament. No es modifica l'estat del
lot ni es crea un correu en fixar aquest contingut.

Les renderitzacions següents reutilitzen la selecció original encara que
s'editi el lot o s'eliminin els banners d'origen. Canviar de plantilla, pòlissa
o lot per a un enviament fixat es rebutja. El camp intern no es pot esborrar o
reescriure per l'ORM públic. Cal un enviament nou per a una campanya nova.
La còpia d'un enviament elimina el snapshot, la referència al correu i la data
d'enviament, i deixa el nou registre obert; no copia el contingut binari adjunt.

Això **no congela les dades econòmiques o personals** de la pòlissa: els càlculs
es tornen a fer amb les dates guardades i les dades disponibles. Una modificació
retroactiva de tarifes o de dades del contracte exigeix revisar el reenviament.
No es promet una còpia binària idèntica del correu original.

## Components i compatibilitat

Els components estan a `report/mailcanvipreus/`:

- `campaign.mako`: estructura i capçalera/peu comuns.
- `warning.mako`: modificació contractual, abans de la salutació.
- `prices.mako`: comparativa d'energia/potència, indexada, autoconsum i Generation kWh.
- `estimation.mako`: imports i explicacions dels orígens de consum.
- `legal.mako`: informació contractual, CNMC, documentació i opcions de canvi/baixa.

Els decimals comparteixen les mateixes rutes de format que `get_data()`.
L'estimació indexada accepta les dates explícites i el mapa fiscal del backend;
fora d'aquest circuit conserva els valors per defecte històrics. La resta de
càlculs conserva la fórmula i els arrodoniments; en el circuit de campanya el
context es copia per no contaminar el càlcul següent i les dates també s'apliquen
al bo social. Els altres cridadors mantenen el comportament històric.
El percentatge d'impost elèctric mostrat prové del backend, no d'un literal.

El bloc legal de períodes prové de `correu-canviPreus202610.mako`; per a indexada
es conserva la referència específica existent a `correu-canviPreus202601.mako`.
Això no acredita que textos, enllaços o clàusules continuïn vigents: cal revisió
jurídica abans d'activar qualsevol modalitat, inclosos els enllaços històrics
que apunten a dominis de prova. No s'han inventat ni aprovat clàusules noves.

### PDF

El report des de pòlissa pot rebre `price_change_enviament_id` al context.
Valida que l'enviament pertanyi a aquella pòlissa i renderitza la plantilla del
seu lot sobre l'objecte d'enviament real. Si no es proporciona, només selecciona
un enviament de canvi de preus quan l'associació és única; davant absència o
ambigüitat demana l'identificador explícit. Les plantilles antigues declarades
realment sobre pòlissa mantenen aquell contracte.

El renderer comprova el resultat PDF, propaga errors del procés i neteja els
fitxers temporals. La generació real amb Puppeteer/Chromium s'ha provat amb dades
sintètiques, comprovant que l'HTML coincideix exactament amb el de Poweremail i
que el PDF conté dates, contingut editorial i informació legal.

## Actualització d'instal·lacions existents

La migració és
`migrations/5.0.25.5.0/post-0003_add_price_change_campaign.py`.
Inicialitza els camps del lot i de l'enviament i carrega permisos, configuració
i vistes. La versió coincideix amb la que informa l'entorn ERP utilitzat.
La dependència `report_banner_poweremail` és explícita al manifest.

No s'escriu `canviPreusBackend`, que és `noupdate=1`. La nova plantilla i els
esborranys tenen IDs propis. La càrrega de la migració és idempotent i no
sobreescriu personalitzacions dels nous registres `noupdate` ja existents.
No s'assigna la nova plantilla a lots existents ni s'activa cap campanya.

S'ha executat el generador de migracions en mode `--dry-run`. Compara contra el
`main` local i no incorpora els fitxers nous encara no versionats: el resultat
contenia candidats aliens a aquest canvi. No se n'ha aplicat cap. S'ha revisat
manualment el diff de camps, manifest, XML i permisos; el test de migració real
l'executa dues vegades i comprova la conservació de les dues plantilles.

## Verificació i límits

La sincronització prèvia del workspace s'ha omès per **excepció expressa de
l'usuari**. S'utilitzen dependències locals; no s'ha modificat el repositori
GISCE ERP ni les seves refs. Els tests només redirigeixen temporalment els dos
addons Som Energia mitjançant el wrapper amb lock i restauració.

Vegeu `price-change-verification.md` per a resultats, comparació amb la base i
matriu de cobertura. No s'han provat clients reals de correu ni s'han enviat
missatges. Les revisions de negoci, jurídica, enllaços i adjunts reals continuen
sent requisits previs a l'activació, no aprovacions implícites d'aquests tests.
