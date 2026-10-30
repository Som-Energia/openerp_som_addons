# Correu reutilitzable de canvi de preus

## Abast

La plantilla optativa
`som_polissa_condicions_generals.price_change_campaign_template` separa els
textos editorials dels càlculs. Reutilitza `report.banner` i el backend de
canvi de preus. No modifica cap plantilla històrica ni activa enviaments.

No afegeix herències sobre `poweremail.templates`, `report.banner`,
`ir.translation`, `som.infoenergia.lot.enviament` o `som.enviament.massiu`.
Tampoc afegeix models, camps al lot/enviament, snapshots, rols editorials ni
restriccions als permisos o al contingut dels banners.

## Dates i reenviaments

La selecció dels banners utilitza la data del dia en què es prepara/envia el
correu. La previsualització fa servir la data del dia en què s'executa.
No hi ha una data de campanya guardada al lot.

Els preus actuals es calculen per aquell mateix dia. L'entrada en vigor dels
preus nous es resol amb el mecanisme del backend: la primera versió activa
futura de la llista de preus o, si no n'hi ha, el valor històric de 60 dies.
L'assumpte i el cos utilitzen aquesta mateixa resolució. Aquesta data futura
és la dels preus nous, no la data de selecció dels banners.

Cada renderització consulta les dades i els banners vigents. No es fixa cap
contingut en previsualitzar, no s'escriu al lot/enviament i un reenviament no
conserva automàticament els textos d'una renderització anterior. Les còpies
d'enviaments mantenen el comportament estàndard.

## Banners i traduccions

| Codi | Ús |
| --- | --- |
| `CANVI_PREUS_MOTIU` | Motiu del canvi; variants 2.0TD/resta |
| `CANVI_PREUS_AUTOCONSUM` | Compensació simplificada en modalitat per períodes |
| `CANVI_PREUS_COMIAT` | Comiat |

El backend crida `report.banner.get_report_banners()` amb la referència de la
plantilla Poweremail, la data actual i l'ID real de l'enviament massiu. Els
dominis poden seleccionar sobre l'enviament i la seva `polissa_id`.

La vigència, l'ordre de prioritat, les traduccions i el fallback són els que
ja ofereix el model de banners. No s'exigeixen traduccions duplicades en totes
dues llengües ni es rebutgen solapaments que el mecanisme estàndard resol per
prioritat. S'utilitzen les pantalles i permisos habituals de Banner Manager.
No hi ha menús o grups editorials nous.

L'HTML dels banners s'insereix com a contingut: no es torna a compilar com a
Mako ni s'hi aplica una allowlist nova d'etiquetes, atributs o estils. Cal
revisar-ne la presentació i el contingut abans d'enviar.

Els quatre esborranys inicials tenen vigència `2099-01-01` a `2099-01-01`, per
no activar-los accidentalment. Cal preparar-los amb les eines habituals abans
d'enviar. La configuració té IDs propis i `noupdate=1`.

## Preparació i enviament

1. Preparar textos, traduccions, vigències i dominis dels banners.
2. Crear un lot normal amb la plantilla reutilitzable i el remitent adequat.
3. Preparar els adjunts amb el circuit existent. No s'afegeix una comprovació
   nova que exigeixi exactament un PDF; cal verificar l'adjunt que anuncia el
   text i recordar que el circuit massiu existent selecciona el primer adjunt.
4. Previsualitzar i revisar assumpte, imports, textos, destinataris, CC/BCC,
   adjunts i variants aplicables abans d'autoritzar l'enviament.

Poweremail manté el seu tractament habitual dels errors: pot capturar una
excepció de renderització i retornar contingut buit. Aquesta funcionalitat no
sobreescriu `get_mailbox_values()` per canviar-ho. Els cridadors que ja passin
`raise_exception=True`, com el circuit de previsualització, conserven aquesta
opció estàndard. No es promet una validació atòmica de tot el lot.

## Càlculs, PDF i desplegament

L'estimació indexada pot rebre el mapa fiscal de la pòlissa perquè els impostos
coincideixin amb la resta del correu. Sense aquest paràmetre conserva els valors
històrics. No es canvien les fórmules ni els arrodoniments per aquesta review.

El PDF renderitza el cos HTML de la mateixa plantilla del lot sobre l'enviament
real. Es pot seleccionar amb `price_change_enviament_id` al context; el report
comprova que pertanyi a la pòlissa. Sense identificador explícit exigeix una
associació única. Això no afegeix camps als models compartits.

La migració `5.0.25.5.0/post-0003_add_price_change_campaign.py` carrega la nova
plantilla, dominis, esborranys i permís de lectura del backend PDF propi. No
inicialitza camps de lots/enviaments ni carrega vistes editorials. Cal
actualitzar el mòdul i reiniciar els processos ERP/workers si encara carreguen
una revisió anterior d'aquesta PR. No s'eliminen columnes de DB de proves
anteriors automàticament.

El POT es conserva exactament com abans de la PR: no se'n regeneren entrades.
La ubicació dels nous Mako encara està pendent de discussió; no s'han mogut ni
duplicat. Vegeu `price-change-review.md` i `price-change-verification.md`.

No s'han enviat correus reals. La revisió funcional/jurídica, els enllaços,
els adjunts i les proves en clients reals continuen pendents abans d'activar
cap enviament.
