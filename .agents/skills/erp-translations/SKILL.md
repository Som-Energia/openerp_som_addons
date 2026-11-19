---
name: erp-translations
description: >
  Afegeix, actualitza i diagnostica traduccions d'OpenERP 5 de Som Energia:
  Python, XML, reports Mako, catàlegs PO/POT, context d'idioma i migracions.
  Trigger: Quan cal traduir textos de l'ERP, corregir textos que surten en un
  altre idioma, modificar i18n o recarregar traduccions catalanes/castellanes.
metadata:
  version: "1.0"
---

# Traduccions OpenERP / Som Energia

## Resultat esperat

Una traducció no està acabada quan existeix al `.po`: ha de correspondre al
**text font exacte**, estar associada al recurs correcte, carregar-se a
`ir.translation` i aparèixer amb l'idioma correcte en el flux real.

Consulta [references/pr-patterns.md](references/pr-patterns.md) per als diffs
que fonamenten aquesta recepta i els punts d'implementació que cal revisar si
canvia la versió de l'ERP. Les PRs són exemples, no una política immutable.

## 1. Delimitar la tasca abans d'editar

- Llegeix l'`AGENTS.md` del checkout objectiu, identifica'l amb
  `git rev-parse --show-toplevel` i revisa `git status --short --branch`.
  Respecta l'elecció explícita de checkout/worktree i la política de branques.
- Identifica mòdul, text, pantalla/report/correu, idioma font i idiomes destí.
  Si no es poden deduir amb certesa de la petició i del codi, pregunta-ho.
- No assumeixis que el font és anglès: hi ha literals catalans, castellans i
  anglesos. Comprova els codis reals (`ca_ES`, `es_ES`, etc.), no creïs `ca.po`
  o `es.po` a partir d'un exemple genèric de documentació.
- Per textos legals, combina aquesta skill amb
  [update-contract-report](../update-contract-report/SKILL.md): contingut i
  terminologia aprovats manen; no reescriguis clàusules per iniciativa pròpia.
- Abans de canviar models/XML o crear una migració, llegeix
  [erp-migration](../erp-migration/SKILL.md). No modifiquis backend, dades o
  dependències compartides si només cal corregir el catàleg.

Des de l'arrel del checkout seleccionat, substitueix els exemples pel mòdul i
el text reals:

```bash
MODULE=som_polissa_condicions_generals
find "$MODULE/i18n" -maxdepth 1 -type f
rg -n -F 'DADES DEL PUNT DE SUBMINISTRAMENT' "$MODULE"
rg -n 'trans_load|load_translations' "$MODULE/migrations"
```

## 2. Identificar el mecanisme, no traduir a cegues

| On viu el text | Què cal inspeccionar |
|---------------|----------------------|
| Python | Import de `tools.translate._`, literal dins `_()`, interpolació posterior i `context['lang']` al lloc de la crida. |
| Camps, seleccions, vistes i dades XML | Metadades del model i referències exportades `field:`, `help:`, `selection:`, `view:` o `model:`; l'etiqueta no és el nom tècnic. |
| Report `.mako` amb `${_(...)}` | Literal, components inclosos, referències `rml:`, catàlegs i idioma del render. |
| Correu o plantilla amb branques CA/ES | Selecció d'idioma i cossos ja localitzats. No convertir automàticament un mecanisme bilingüe en gettext. |
| Diccionari explícit de noms localitzats | Regla del flux i fallback; no és necessàriament una entrada de catàleg. |

No tradueixis noms de camps, XML IDs, claus de selecció, noms tècnics de
reports, variables ni valors d'API. `translate=True` serveix per a valors
traduïbles d'un camp; no l'afegeixis simplement per traduir-ne l'etiqueta.

Patró Python (dins del mètode que disposa del context adequat):

```python
from tools.translate import _

message = _(u"No s'ha trobat el contracte %s") % contract_name
```

Patró Mako:

```mako
${_(u"Terme energia (€/kWh)")}
${_(u"Contracte %s") % contract_name}
```

Tradueix **abans** d'interpolar: no facis `_(text % valor)`,
`_(text.format(valor))` ni `_()` sobre una cadena construïda dinàmicament.
Conserva compatibilitat Python 2.7/3 i Unicode; no introdueixis f-strings.

## 3. Actualitzar font, POT i PO coherentment

- `<modul>/i18n/<modul>.pot`: inventari de literals i referències; els
  `msgstr` de les entrades són buits. La capçalera és metadada, no una entrada
  pendent de traduir.
- `<modul>/i18n/<locale>.po`: mateixos literals/referències i traducció a
  `msgstr`. **Modificar només el POT no canvia el text que veu l'usuari.**
- Si només corregeixes una traducció existent, canvia el `msgstr` del PO;
  no cal tocar el POT si el font i les referències no han canviat.
- Si afegeixes/canvies el font o mous un component, actualitza POT i els PO
  afectats. Conserva traduccions vàlides i limita el diff a l'abast acordat.

### Actualització puntual

Busca primer l'entrada existent. Afegeix-hi les referències que falten; no
creïs entrades duplicades per cada fitxer. Exemple de la PR #1501, al PO:

```po
#: rml:som_polissa_condicions_generals/report/components/contact_info.mako:26
#: rml:som_polissa_condicions_generals/report/components/summary_identification.mako:19
msgid "DADES DEL PUNT DE SUBMINISTRAMENT"
msgstr "DATOS DEL PUNTO DE SUMINISTRO"
```

Al POT, el mateix bloc té `msgstr ""`. Recalcula les línies sobre el checkout
actual: aquests números només il·lustren el diff històric.

Les referències `#:` **no són comentaris prescindibles** per al carregador
OpenERP: codifiquen tipus, recurs i identificador. Conserva els prefixos
exportats (`code:addons/...`, `rml:<modul>/report/...`, etc.). En moure o
reutilitzar un component, revisa totes les ubicacions; no confiïs en un
fallback per text d'una altra plantilla. El lookup pot variar segons la
versió de l'ERP.

### Reexportació àmplia

Quan hi ha moltes cadenes noves, exporta des d'un ERP local amb el mòdul
instal·lat/actualitzat i el codi correcte. L'assistent
`wizard.module.lang.export` combina l'exportació ERP amb
`append_report_translations` per als Mako. Exporta **un sol mòdul** com a
plantilla POT (sense idioma); l'afegit de reports s'omet per diversos mòduls
o si el format intern no és `pot`.

Revisa `<modul>/i18n/babel.cfg` si hi ha reports Mako. Patró existent:

```ini
[mako: **.mako]
input_encoding = utf-8
encoding = utf-8
```

Una extracció genèrica amb `xgettext`/`pybabel` o només `trans_export` no
substitueix aquest flux complet: pot perdre metadades ERP o textos de reports.
Llegeix la implementació instal·lada abans d'automatitzar l'exportació.
Fusiona el resultat amb els PO conservant traduccions revisades; inspecciona
entrades noves, eliminades, duplicades i `fuzzy`. No regeneris tots els
catàlegs del repositori ni canviïs symlinks compartits per fer l'exportació.
Si no pots garantir que l'ERP llegeix el worktree correcte, atura't.

### Regles d'integritat del text

- `msgid` ha de coincidir amb el literal **concatenat**: accents, majúscules,
  espais inicials/finals, salts de línia, puntuació i HTML inclosos.
- Les línies PO entre cometes es concatenen sense afegir espais. Un
  `msgstr ""` seguit de continuacions no és una traducció buida.
- Mantén placeholders (`%s`, `%d`, `%(name)s`, `{}`, `{0}`, `{name}`), els seus
  tipus i el nombre d'arguments. No canviïs l'ordre de placeholders
  posicionals anònims. Conserva `${...}`, escapes i expressions Mako.
- Tradueix el text visible sense trencar etiquetes, atributs, enllaços,
  unitats, fórmules o imports. Si canvia l'HTML del font, sincronitza el
  `msgid`; el canvi pot deixar de trobar la traducció antiga (PR #1518).
- Reutilitza terminologia del mòdul i revisa el sentit complet en CA/ES.
  No omplis amb el font totes les entrades pendents només per passar tests.
- Revisa `fuzzy` manualment i retira la marca només quan la traducció sigui
  correcta. No assumeixis que el carregador antic filtra aquestes entrades.

## 4. Comprovar l'idioma en execució

Un PO correcte no arregla un context incorrecte. Traça l'idioma des de la
persona destinatària/contracte/factura fins al render i els seus helpers;
no assumeixis que l'idioma de l'usuari que executa l'acció és el desitjat.

En aquest ERP, `tools.translate._` inspecciona el frame que el crida per
obtenir la variable local `context`. Un helper pot perdre l'idioma encara
que el mètode pare el tingui. La PR #1398 estableix
`context = {'lang': get_lang_partner(fact)}` dins de diversos helpers de
factura. Reutilitza el patró real del mòdul; si ja hi ha context, copia'l i
conserva les altres claus. No eliminis una variable `context` aparentment
no usada sense comprovar aquest ús indirecte.

No afegeixis un diccionari paral·lel de traduccions com a pegat per un PO,
referència o context incorrectes. Els noms de documents de la PR #1466 són
un cas específic de localització explícita, no el patró general.

## 5. Preparar la càrrega a instal·lacions existents

Per canvis de catàleg en un mòdul instal·lat, prepara una migració `post-...`
que carregui els PO afectats amb `trans_load`, com a les PRs #1501 i #1518.
També cal carregar-los si només has afegit referències a una traducció que
ja existia. Un mòdul nou no necessita una migració d'instal·lacions prèvies;
cal comprovar que la instal·lació carrega els idiomes previstos.

Segueix `erp-migration` per versió i número. Revisa primer:

```bash
python scripts/create_migration_script.py --dry-run
```

**Límits actuals del generador que has de verificar abans d'usar-lo:**

- Compara amb el `main` **local**, que pot estar endarrerit respecte de la
  base de la PR. Contrasta el candidat amb `git diff origin/main...HEAD` i
  els canvis locals (`git diff HEAD`); no generis migracions d'altres PRs.
- `TARGET_VERSION` és una decisió manual, no la versió del manifest ni la
  data d'avui. Confirma la versió instal·lada abans d'escollir directori.
- Detecta PO, però actualment només emet `trans_load` per `i18n/es_ES.po`.
  Per `ca_ES` o altres idiomes cal completar el candidat manualment.
- No sobreescriguis migracions existents ni afegeixis `_auto_init` o càrrega
  d'XML si no ho requereix el canvi real.

Plantilla mínima (substitueix mòdul i idioma; repeteix la càrrega per cada
PO afectat):

```python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from tools import config
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    module_name = 'som_polissa_condicions_generals'
    logger.info('Updating translations')
    trans_load(
        cursor,
        '{}/{}/i18n/es_ES.po'.format(config['addons_path'], module_name),
        'es_ES'
    )


def down(cursor, installed_version):
    pass


migrate = up
```

No executis càrregues contra producció ni contra una base compartida sense
autorització. Prova la migració en una base local destinada a validació,
seguint `erp-migration`/`erp-start` i les restriccions de worktrees. Verifica
el fitxer que resol `addons_path` i els logs: `trans_load` pot registrar un
fitxer absent sense llançar excepció. La càrrega no garanteix que totes les
caches dels processos vius es refresquin; comprova el resultat en un procés
nou i documenta si cal reiniciar serveis, sense fer-ho automàticament.

## 6. Validar en tres nivells

### Catàleg i diff

```bash
git diff --check
git diff -- "$MODULE/i18n" "$MODULE/migrations"
# Si GNU gettext està disponible; repetir per cada PO modificat:
msgfmt --check --check-format -o /dev/null "$MODULE/i18n/es_ES.po"
```

Amb un parser PO disponible (Babel/polib), comprova sintaxi, duplicats,
entrades afectades absents/buides, `fuzzy`, referències i placeholders.
No instal·lis dependències sense acord ni consideris `msgfmt` una prova del
lookup ERP. Revisa també els formats `{...}` i `${...}` manualment: no
estan necessàriament coberts per `--check-format`.

### Extracció i cobertura amb Destral

Llegeix [erp-test](../erp-test/SKILL.md), prepara virtualenv, `WORKSPACE` i
PostgreSQL/MongoDB/Redis. Des del worktree seleccionat:

```bash
PYENV_VERSION=erp scripts/run-tests-worktree.sh \
    --addon "$MODULE" -- --no-requirements -m "$MODULE" \
    -t OOBaseTests.test_translate_modules
```

Declara amb `--addon` tots els addons modificats que el test hagi d'utilitzar.
No executis `run-tests.sh` directament en un worktree ni toquis els enllaços.

El test exporta un POT temporal, inclou els reports i comprova literals
absents i traduccions buides. Si `DESTRAL_TESTING_LANGS` és buit, retorna
sense validar-los. El runner del repositori actualment fixa
`['en_US', 'ca_ES', 'es_ES']`: no prometis limitar-ho amb una variable externa
que el runner sobreescriurà. Si fallen catàlegs preexistents fora d'abast,
separa aquests errors dels nous i informa'n; no els amaguis ni inventis
traduccions per fer passar el test.

### Comportament real i upgrade

- Verifica que la migració carrega els registres esperats i que un procés
  nou resol el text traduït amb l'idioma destí.
- Renderitza el report/correu o obre la vista en CA i ES amb dades de prova,
  segons l'abast: inclou components reutilitzats, branques condicionals i
  interpolacions. No enviïs correus ni iniciïs signatures reals.
- Si canvies Python/XML, executa els tests del mòdul i valida l'upgrade;
  per la migració, comprova sintaxi Python 2.7 i 3 segons `erp-migration`.
- El test de catàlegs **no valida** totes les ubicacions `rml:`, l'idioma
  dels helpers, la càrrega de la migració ni el PDF final. No el substitueixis
  per una cerca de text o un test amb el traductor mockejat.

## Checklist de sortida

- [ ] Mòdul, mecanisme, font i idiomes identificats; abast respectat.
- [ ] Font/POT/PO coherents; referències correctes i sense duplicats nous.
- [ ] Placeholders, Unicode, HTML i terminologia revisats.
- [ ] Context d'idioma comprovat al flux i als helpers afectats.
- [ ] Càrrega dels PO prevista per cada idioma i versió de migració confirmada.
- [ ] Validacions estàtiques, Destral i prova funcional: resultats diferenciats.
- [ ] Informats els fitxers canviats, com aplicar-los, si cal reinici i què
      queda pendent. No marcar tests o renderitzacions no executats com a fets.
