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
    └── X.XX.X/              # Versió actual (ex: 1.2.3)
        ├── pre.py           # S'executa ABANS de l'_auto_init del model
        ├── post.py          # S'executa DESPRÉS de l'_auto_init del model
```

## Workflow

### Pas 1: Crear l'estructura

Si el directori `migrations` no existeix:
```bash
mkdir -p <nom_modul>/migrations/X.XX.X/
```

On `X.XX.X` és la versió actual del mòdul (obtinguda de `__init__.py` o `__openerp__.py`).

### Pas 2: Generar script (opcional)

```bash
python /scripts/gen_migration.py <nom_modul>
```

### Pas 3: Escriure el script

**pre.py** — s'executa ABANS de l'_auto_init:
```python
# -*- coding: utf-8 -*-
from tools import migrate


def migrate(cr, version):
    # Crear columna manualment si cal
    cr.execute("""
        ALTER TABLE som_my_model
        ADD COLUMN new_field varchar;
    """)
```

**post.py** — s'executa DESPRÉS de l'_auto_init:
```python
# -*- coding: utf-8 -*-
from tools import migrate


def migrate(cr, version):
    # Actualitzar valors del camp nou
    cr.execute("""
        UPDATE som_my_model
        SET new_field = 'default_value'
        WHERE new_field IS NULL;
    """)
```

## Quan utilitzar pre.py vs post.py

| Script | Quan usar |
|--------|-----------|
| **pre.py** | Camps que triguen molt a crear-se (ex: camps calculats/stored). Crear columna manualment a PostgreSQL abans de l'_auto_init. |
| **post.py** | Canvis normals que necessiten executar-se DESPRÉS del model. Actualitzar valors per defecte. |

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
