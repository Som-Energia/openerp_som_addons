---
name: erp-test
description: >
  Executa tests de mòduls OpenERP/Som Energia utilitzant destral.
  Automatitza: verificar contenidors, executar scripts/run-tests.sh.
  Trigger: Quan necessites executar tests d'un mòdul OpenERP amb destral.
metadata:
  author: oriol
  version: "1.1"
---

## When to Use

Utilitza aquesta skill quan:
- Necessites executar tests d'un mòdul OpenERP del projecte
- Vols automatitzar el workflow de testing local
- Estàs desenvolupant un mòdul i necessites TDD

## Configuració Requerida

Aquesta skill requereix:
1. **Virtualenv activat** (pyenv, venv, o equivalent) amb destral instal·lat
2. **Contenidors Docker**: PostgreSQL, MongoDB, Redis

## Workflow

### Pas 1: Verificar Contenidors

```bash
docker ps --format "{{.Names}}" | grep -E "postgres|redis|mongo"
```

Contenidors esperats:
- PostgreSQL (src_db_1)
- MongoDB (src_mongo_1)
- Redis (src_redis_1)

### Pas 2: Executar tests

```bash
scripts/run-tests.sh <database> -m <module_name>
```

**Exemple**:
```bash
scripts/run-tests.sh test_som_polissa -m som_polissa
```

Test únic:
```bash
scripts/run-tests.sh test_som_polissa -m som_polissa -t TestsClass.test_method
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| `destral: command not found` | Virtualenv no activat | Activa el teu virtualenv |
| `Connection refused to localhost:5432` | PostgreSQL no corrent | `docker-compose up -d` |
| `Connection refused to localhost:27017` | MongoDB no corrent | `docker-compose up -d` |
| `Connection refused to localhost:6379` | Redis no corrent | `docker-compose up -d` |
| `Database does not exist` | DB no creada | destral la crea automàticament |
| `timeout` | Tests molt lents | Els tests d'OpenERP poden trigar 10+ min |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-apply`: Per verificar que el codi implementat passa els tests
- `sdd-verify`: Per validar contra specs

El test runner detectat és: `scripts/run-tests.sh` (wrapper de destral)
