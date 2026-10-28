# Revisió d'arquitectura de la campanya de canvi de preus

Seguiment de la review de la PR 1508. Cal distingir les correccions aplicades
ara de les alternatives pendents d'acord: aquesta nota no aprova les
sobreescriptures que encara es conserven.

## Correccions aplicades

- S'elimina `i18n/som_polissa_condicions_generals.pot`, no només les entrades
  afegides per la campanya. Això no elimina els textos CA/ES dels banners ni
  el catàleg `.po` existent. No cal generar un POT per preparar una campanya.
- S'elimina `models/price_change_translation.py` i el seu import. El mòdul ja
  no hereta `ir.translation`: crear, editar o eliminar traduccions torna a
  seguir els permisos i el comportament habituals d'OpenERP, sense condicions
  addicionals per pertànyer al grup editorial.
- La validació de contingut de campanya es manté a `_campaign_banners()` i
  `validate_banner_candidates()`, abans d'escriure el snapshot. Es comproven
  explícitament totes dues llengües, absències, duplicats i HTML no executable.
  Escriure una traducció invàlida per l'ORM estàndard pot tenir èxit; seleccionar
  aquella campanya o renderitzar-ne el correu ha de fallar. És un control al
  punt de consum, no un control global de l'editor de traduccions.
- `som.enviament.massiu.copy()` només reinicialitza estat, data, correu i
  snapshot quan l'original té un snapshot. Abans també alterava les còpies
  d'enviaments aliens a la campanya, inclosos els valors passats a `default`.
  Sense snapshot es delega la còpia habitual sense modificar aquests valors.

No hi ha camps, taules, ACL ni recursos XML nous en aquestes correccions.
Retirar una herència només de mètodes no necessita migració de dades; sí que
cal reiniciar els processos ERP/workers perquè deixin de carregar-la. La
migració de la funcionalitat inicial es conserva: inicialitza els camps de
lot/enviament i carrega seguretat, dades i vistes. No carrega el POT.

## Per què es va canviar el càlcul fiscal

`som_indexada/utils.py` aplicava sempre IE 5,11% i IVA 21% a l'estimació
indexada. El backend ja obté el mapa fiscal simplificat de la pòlissa; passar-lo
com a `price_change_taxes` evita mostrar una estimació amb impostos diferents
dels que fa servir la resta del correu, inclòs IGIC quan correspon.

El paràmetre és optatiu: els cridadors que no l'envien mantenen els valors
històrics. Això explica la intenció del canvi acceptat a la review, però no
constitueix una auditoria del tractament fiscal de tots els contractes.

## Inventari de les extensions de `price_change_campaign.py`

### `poweremail.templates.get_mailbox_values`

**Intenció:** Poweremail captura errors de renderització i pot retornar una
cadena buida. El hook activa `raise_exception` per a la plantilla de campanya
i les còpies que inclouen el seu component, per no preparar un correu sense
contingut obligatori.

**Cost i abast:** la sobreescriptura s'executa per a qualsevol plantilla, encara
que només canviï el context de campanya. La detecció per ruta Mako és fràgil i
s'ha de revisar si es mouen les plantilles.

**Alternativa:** propagar errors des dels punts d'entrada de la campanya. Cal
cobrir enviament, còpies de plantilla i previsualitzacions, no només afegir una
validació al backend: Poweremail també en podria silenciar l'excepció. Es manté
provisionalment fins a acordar com es cobreixen tots aquests punts d'entrada.

### `som.infoenergia.lot.enviament`

Només afegeix els tres camps de dates. No sobreescriu cap mètode. Les dates
explícites eviten que el correu depengui del dia en què es renderitza. Moure-les
a un model específic de campanya és possible, però afegeix estructura i no és
necessari per retirar les sobreescriptures globals.

### `report.banner.create/write/unlink`

**Intenció:** limitar el personal editorial a l'HTML dels codis de campanya,
sense permetre canviar dominis, vigències, prioritats ni imatges; rebutjar HTML
executable en editar el banner.

**Problema:** `_is_editor()` identifica la pertinença al grup, no el circuit
que s'està utilitzant. Per tant també pot impedir crear/eliminar altres banners
o gestionar-los a una persona que tingui alhora permisos més amplis. Les
vistes de només lectura no justifiquen imposar aquestes restriccions globals.

**Alternatives pendents d'acord:**

1. Reutilitzar l'edició i permisos habituals dels banners i validar el contingut
   només al circuit de campanya. És l'opció més simple, però no ofereix un rol
   nou estrictament limitat a editar només text.
2. Si aquest rol limitat és imprescindible, donar-li una interfície específica
   de campanya amb una operació d'edició acotada, sense ACL d'escriptura general
   sobre banners ni restriccions globals basades en grup. Requereix revisar
   permisos, vistes i migració; no n'hi ha prou amb un flag al context que el
   client podria enviar lliurement.

Les sobreescriptures de banners es conserven provisionalment, no es donen per
acceptades. Retirar el hook de traduccions no converteix aquest grup en una
barrera de seguretat sobre tot `ir.translation`.

### `som.enviament.massiu.create/write/copy`

- `create()` impedeix proporcionar un snapshot fabricat en crear l'enviament.
- `write()` impedeix reescriure el snapshot i canviar la pòlissa/lot d'un
  enviament que ja l'ha fixat. No valida qualsevol modificació de qualsevol
  enviament: el control es limita als camps i registres afectats.
- `copy()` evita reutilitzar contingut fixat i referències d'enviament en una
  campanya nova. S'ha corregit l'abast perquè no reinicialitzi còpies sense
  snapshot.

La necessitat és conservar la selecció original en reenviar. Una alternativa
és tenir un registre immutable propi, separat de l'enviament. Això permetria
retirar algunes proteccions d'aquest model, però implicaria un canvi de model
i de migració que no s'aplica sense acord.

`_domain_matches()`, `_campaign_banners()`, `_check_price_change_attachment()` i
`_get_price_change_snapshot()` són mètodes nous, no sobreescriptures. Concentren
la selecció, la validació de l'adjunt i la fixació del contingut de campanya.
El bloqueig de fila evita fixar dues seleccions diferents concurrentment;
el snapshot no és una còpia immutable de totes les dades econòmiques.

## Mako: decisió pendent, sense trasllat automàtic

`somenergia-oomakotest` ja és font de plantilles que s'envien a producció via
`oomako upload`; no és només un repositori de fixtures. La PR relacionada és
la 237. En aquest punt la review té sentit.

Ara bé, l'XML de l'addon crea un cos que inclou
`/som_polissa_condicions_generals/report/mailcanvipreus/campaign.mako`, que al
seu torn inclou quatre fitxers. El renderer resol aquestes rutes als addons
del servidor. `oomako upload` puja el cos de la plantilla, no publica aquests
fitxers locals al servidor, i actualment escriu `def_body_text`, mentre que el
PDF llegeix `def_body_html`. La fixture sintètica de la PR 237 no té
`poweremailId` i no s'ha d'usar per carregar contingut a producció.

Opcions per acordar:

- **Conservar els components a l'addon:** manté el desplegament actual i els
  tests poden apuntar al worktree, però manté els Mako en el repo qüestionat.
- **Font única a oomakotest:** preparar una plantilla autocontinguda (o un
  empaquetat explícit dels components) i definir com es publica el mateix cos
  per correu i PDF. L'addon conservaria backend/configuració, no una segona còpia
  dels textos. Cal adaptar inicialització, detecció de la campanya, upload i
  proves de desplegament; no assumir que el simple moviment dels fitxers ho
  resol.

No s'afegeix una dependència de producció del checkout de tests ni es dupliquen
les plantilles. La ubicació final i el mecanisme de publicació continuen
pendents d'acord.
