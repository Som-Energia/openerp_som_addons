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
- Afegeixes un nou camp a un model
- Modifies el tipus d'un camp existent
- Canvies l'estructura d'un model
- Necessites aplicar canvis a producció

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

Aquest script:
- Compara amb la branca `main`
- Detecta canvis en fitxers XML, Python, CSV (security) i PO
- Assigna el següent número seqüencial
- Crea el nom automàticament (ex: `post-0001_IMP_agents_docs_fields_migrate.py`)

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
