---
name: erp-test
description: >
  Executa tests de mòduls Odoo/Som Energia utilitzant destral.
  Automatitza: verificar contenidors, activar pyenv, executar dodestral.
  Trigger: Quan necessites executar tests d'un mòdul Odoo amb destral.
metadata:
  author: oriol
  version: "1.0"
---

## When to Use

Utilitza aquesta skill quan:
- Necessites executar tests d'un mòdul OpenERP del projecte
- Vols automatitzar el workflow de testing local
- Estàs desenvolupant un mòdul i necessites TDD

## Configuració Requerida

Aquesta skill requereix:
1. **Contenidors Docker**: Només PostgreSQL, MongoDB, Redis (Odoo corre al host)
2. **pyenv**: Entorn virtual amb nom `erp` (`pyenv virtualenv erp`)
3. **Odoo instal·lat al host**: A `~/somenergia/src/erp/server/bin`

## Workflow

### Pas 1: Verificar Contenidors (només BBDD)

```bash
docker ps --format "{{.Names}}" | grep -E "postgres|redis|mongo"
```

Contenidors esperats:
- PostgreSQL (src_db_1)
- MongoDB (src_mongo_1)
- Redis (src_redis_1)
- Odoo NO està a Docker — corre al host

### Pas 2: Activar pyenv

```bash
pyenv activate erp
```

O si està configurat amb pyenv-virtualenv:
```bash
source $(pyenv which activate)
```

### Pas 3: Variables d'Entorn

Configurar segons el workflow de GitHub Actions:

```bash
export PYTHONPATH=~/somenergia/src/erp/server/bin:~/somenergia/src/erp/server/bin/addons
export OPENERP_PRICE_ACCURACY=6
export OORQ_ASYNC=False
export OPENERP_DB_HOST=localhost
export OPENERP_DB_USER=erp
export OPENERP_DB_PASSWORD=erp
export OPENERP_MONGODB_HOST=localhost
export OPENERP_REDIS_URL=redis://localhost:6379/0
```

### Pas 4: Executar destral

```bash
dodestral <database> -m <module_name>
```

**Exemple**:
```bash
dodestral test_som_polissa -m som_polissa
```

O amb opcions adicionals:
```bash
destral --report-coverage test_som_polissa -m som_polissa
```

## Usage

### Execució Bàsica

```bash
# Activar entorn i executar tests
pyenv activate erp && dodestral test_db -m som_polissa
```

### Script Wrapper Recomanat

Crear un script a `~/bin/run-erp-test`:

```bash
#!/bin/bash
set -e

MODULE=${1:-som_polissa}
DB_NAME=${2:-test_erp}

# Verificar contenidors
echo "=== Verificant contenidors ==="
docker ps --format "{{.Names}}" | grep -E "postgres|redis|mongo" || {
    echo "ERROR: Contenidors no corrent. Executa 'docker-compose up -d' primer."
    exit 1
}

# Activar pyenv
echo "=== Activant entorn erp ==="
eval "$(pyenv init -)"
pyenv activate erp

# Variables
export PYTHONPATH=~/somenergia/src/erp/server/bin:~/somenergia/src/erp/server/bin/addons
export OPENERP_PRICE_ACCURACY=6
export OORQ_ASYNC=False
export OPENERP_DB_HOST=localhost
export OPENERP_DB_USER=erp
export OPENERP_DB_PASSWORD=erp
export OPENERP_MONGODB_HOST=localhost
export OPENERP_REDIS_URL=redis://localhost:6379/0

# Executar tests
echo "=== Executant tests de $MODULE ==="
dodestral $DB_NAME -m $MODULE
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| `destral: command not found` | pyenv no activat | `pyenv activate erp` |
| `Connection refused to localhost:5432` | PostgreSQL no corrent | `docker-compose up -d` (al directori de BBDDs) |
| `Connection refused to localhost:27017` | MongoDB no corrent | `docker-compose up -d` |
| `Connection refused to localhost:6379` | Redis no corrent | `docker-compose up -d` |
| `Database does not exist` | DB no creada | destral la crea automàticament |
| `timeout` | Tests molt lents | Els tests d'OpenERP poden trigar 10+ min |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-apply`: Per verificar que el codi implementat passa els tests
- `sdd-verify`: Per validar contra specs

El test runner detectat és: `dodestral` (custom Odoo test runner)
