---
name: erp-demo-testcase
description: >
  Genera casos de test XML a la carpeta demo d'un mòdul OpenERP.
  Automatitza: validar mòdul, detectar camps obligatoris, resoldre many2one
  requerits i crear fitxers demo consistents.
  Trigger: Quan necessites afegir casos de test/demo XML a un mòdul OpenERP.
metadata:
  author: oriol
  version: "0.1"
---

## When to Use

Utilitza aquesta skill quan:
- Vols afegir nous casos de test en `demo/*.xml`
- Necessites crear registres d'un model amb camps obligatoris
- El model té dependències (`many2one`) i cal crear prerequisits

## Inputs Requerits

- `module_name`: mòdul objectiu (ex: `www_som`)
- `model_name`: model OpenERP (ex: `res.partner`)
- `record_id_prefix`: prefix d'XML ID (ex: `demo_www_som_partner`)

## Inputs Opcionals

- `optional_fields`: diccionari de camps opcionals a omplir
- `target_file`: fitxer demo concret (ex: `demo/www_som_demo.xml`)
- `create_dependencies`: `true/false` (per defecte `true`)

## Workflow

### 1) Validar context del mòdul

- Verificar que existeix `<module_name>/__init__.py`
- Verificar manifest (`__terp__.py` o equivalent) i carpeta `demo/`
- Si no existeix `demo/`, crear-la

### 2) Descobrir camps obligatoris del model

- Localitzar classe/model Python on es defineix `_columns`
- Identificar camps `required=True`
- Separar:
  - camps simples (`char`, `boolean`, `integer`, `float`, `date`, ...)
  - camps relacionals (`many2one`)

### 3) Resoldre dependències obligatòries

Per cada `many2one required=True`:
- Reutilitzar XML ID existent si ja hi ha un registre vàlid a `demo/`
- Si no existeix, crear registre mínim del model relacionat
- Repetir recursivament fins tancar dependències

### 4) Construir registre demo principal

- Crear `<record id="..." model="...">`
- Omplir tots els camps obligatoris
- Aplicar `optional_fields` del prompt (si n'hi ha)
- Usar `<field name="x" ref="module.xml_id"/>` per many2one

### 5) Escriure/actualitzar XML

- Guardar a `demo/*.xml` (fitxer existent o nou)
- Mantenir IDs estables i únics
- Mantenir ordre: dependències abans del registre principal
- Si cal, registrar el fitxer demo al manifest del mòdul

### 6) Validacions finals

- No hi ha `ref` trencats
- No hi ha XML IDs duplicats
- Tots els `required=True` estan coberts
- El fitxer XML és ben format

## Output Contract

Retornar sempre:
- Fitxer(s) tocats (`path`)
- XML IDs creats/reutilitzats
- Llista de dependències creades
- Camps obligatoris detectats
- Decisions preses (defaults, reutilització, exclusions)

## Guardrails

- No modificar dades fora del mòdul objectiu
- No inventar camps: només `_columns` reals del model
- Si falta context funcional per omplir un camp obligatori, preguntar a l'usuari
- Evitar side effects: només canvis a fitxers demo/manifest

## Exemple d'ús

- "Afegeix un cas demo al mòdul `www_som` pel model `res.partner`, amb camp opcional `email`"
- "Crea registre demo per `giscedata.polissa` i resol les dependències obligatòries"
