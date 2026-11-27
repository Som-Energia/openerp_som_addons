---
name: erp-migration
description: >
  Crea scripts de migració per a mòduls OpenERP quan es modifiquen models o fitxers XML.
  Automatitza: generar estructura, plantilla, executar migració.
  Trigger: Quan necessites crear un script de migració, modificar el model, o actualitzar un mòdul a producció.
metadata:
  author: oriol
  version: "1.0"
---

## When to Use

Utilitza aquesta skill quan:
- Afegeixes un model nou o un camp a un mòdul existent, encara que el model sigui nou
- Modifies el tipus d'un camp existent
- Canvies l'estructura d'un model existent
- Necessites aplicar canvis a producció

No és obligatori crear una migració quan la PR parteix d'un mòdul nou, perquè no hi ha instal·lacions existents que actualitzar.

## Estructura de Migracions

Els scripts de migració viuen a:
```
<mòdul>/
└── migrations/
    └── X.XX.X/              # Versió actual (ex: 5.0.25.5.0)
        └── post-0001_<descripcio>.py    # S'executa DESPRÉS de l'_auto_init
```

## Format del Nom de l'Script

```
<tipus>-<número>_<descripció>.py
```

- **tipus**: `pre` (abans) o `post` (després de l'_auto_init)
- **número**: 4 digits, seqüencial (0001, 0002, ...)
- **descripció**: 3-5 paraules separades per `_`

Exemple: `post-0001_add_camp_actiu.py`

## Workflow

### Pas 1: Executar l'script automàtic (RECOMANAT)

L'script `scripts/create_migration_script.py` genera automàticament l'script de migració detectant els fitxers modificats:

```bash
python scripts/create_migration_script.py
```

Preview the proposed migration actions without changing files:

```bash
python scripts/create_migration_script.py --dry-run
```

### Ordre dels recursos i casos que requereixen revisió manual

El generador llegeix `__terp__.py` com un diccionari literal, sense executar-lo.
Selecciona només els recursos modificats i conserva l'ordre de `init_xml` i,
a continuació, `update_xml`. XML i CSV de seguretat no s'agrupen per extensió:
les referències poden requerir que estiguin intercalats. L'ordre de `git diff`
o l'ordre alfabètic dels noms no són un ordre de càrrega vàlid.

Si falta el manifest, no és literal o hi ha recursos modificats que no hi
consten, tant la generació com `--dry-run` s'aturen amb un error abans d'escriure
cap migració. Reviseu el cas i escriviu una migració explícita si és necessari.
No afegiu XML exclusius d'una migració al manifest només per evitar aquest error:
això en canviaria el comportament en les instal·lacions i actualitzacions normals.

Per defecte, manteniu l'ordre del manifest també en les migracions manuals.
Per exemple: configuracions abans de tasques, i tasques abans dels passos que
les referencien. Qualsevol excepció ha d'estar justificada i coberta per un test
d'actualització. El generador no és un analitzador de totes les dependències XML.

Existing migration scripts are never overwritten by default. Use `--replace`
only after reviewing the generated candidate and confirming replacement is safe:

```bash
python scripts/create_migration_script.py --replace
```

Aquest script:
- Compara amb la branca `main`
- Detecta canvis en fitxers XML, Python, CSV (security) i PO
- Assigna el següent número seqüencial
- Crea el nom automàticament (ex: `post-0001_IMP_agents_docs_fields_migrate.py`)

`TARGET_VERSION = "5.0.25.5.0"` in the generator is intentionally the manual
source of truth. Update it when the installed ERP migration version changes;
do not auto-detect the version.

### Pre-Commit Checklist (quan cal migració)

- [ ] Reconcile the complete PR diff: changed model fields have corresponding `_auto_init` actions.
- [ ] Reconcile XML and security changes: every required resource has a `load_data` action.
- [ ] Verify changed manifest resources are included in the migration review.
- [ ] Run and review `python scripts/create_migration_script.py --dry-run`.
- [ ] Run Python 2.7 and Python 3 syntax compilation for the generator and generated migration script.
- [ ] Verify the module upgrade in an ERP environment. For new records with
  external-ID references, test an existing installation without those records,
  execute the migration and check all links. A fresh install uses manifest order
  and does not prove the migration's load order is correct.
- [ ] Execute the migration a second time and check idempotence: no duplicated
  records or lost customizations.
- [ ] Confirm `TARGET_VERSION` still matches the installed ERP migration version; update it manually when it changes.

### Pas 2: Crear manualment (si cal)

Si necessites crear un script manualment:

1. Crear l'estructura:
```bash
mkdir -p <nom_modul>/migrations/5.0.25.5.0/
```

2. El nom segueix el format: `pre-0001_<descripció>.py` o `post-0002_<descripció>.py`

### Pas 3: Escriure el contingut

**post-0001_add_field.py** — s'executa DESPRÉS de l'_auto_init:
```python
# -*- coding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Migration description here")

    # Actualitzar valors del camp nou
    cursor.execute("""
        UPDATE som_my_model
        SET new_field = 'default_value'
        WHERE new_field IS NULL;
    """)


def down(cursor, installed_version):
    pass


migrate = up
```

**pre-0001_create_column.py** — s'executa ABANS de l'_auto_init:
```python
# -*- coding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    cursor.execute("""
        ALTER TABLE som_my_model
        ADD COLUMN new_field varchar;
    """)


def down(cursor, installed_version):
    pass


migrate = up
```

## Quan utilitzar pre vs post

| Tipus | Quan usar |
|-------|-----------|
| **pre** | Camps que triguen molt a crear-se (ex: camps calculats/stored). Crear columna manualment a PostgreSQL abans de l'_auto_init. |
| **post** | Canvis normals que necessiten executar-se DESPRÉS del model. Actualitzar valors per defecte, carregar XMLs, traduccions. |

## Tests del generador

Els tests aïllats formen part de la CI `Local validation scripts` i no necessiten
ERP, PostgreSQL, MongoDB ni Redis:

```bash
scripts/tests/create-migration-script-test.sh
PYENV_VERSION=erp TEST_PYTHON=python scripts/tests/create-migration-script-test.sh
```

Comproven l'ordre del manifest (també XML/CSV intercalats), els recursos no
modificats, la sortida de `--dry-run`, els errors sense escriptures parcials i
la protecció de migracions existents. Aquests tests no substitueixen el test
d'actualització del mòdul afectat.

## Executar la migració

```bash
# Executar només scripts de migració
erpserver -d <nom_bbdd> --run-scripts=<nom_modul>

# Actualitzar mòdul (inclou migracions)
erpserver -d <nom_bbdd> --update=<nom_modul>
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| `relation "table" does not exists` | Taula no creada encara | Verificar que el model s'inicialitza abans |
| `column "x" already exists` | Camp ja creat | Comprovar si és migració duplicada |
| `version not found` | Versió incorrecta | Verificar la versió a `__openerp__.py` |
