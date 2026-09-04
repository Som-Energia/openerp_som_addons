---
name: erp-test
description: >
  Executa tests de mòduls OpenERP/Som Energia utilitzant destral.
  Automatitza: verificar contenidors i executar el wrapper segur de tests.
  Trigger: Quan necessites executar tests d'un mòdul OpenERP amb destral.
metadata:
  author: oriol
  version: "1.2"
---

## When to Use

Utilitza aquesta skill quan:
- Necessites executar tests d'un mòdul OpenERP del projecte
- Vols automatitzar el workflow de testing local
- Estàs desenvolupant un mòdul i necessites TDD

## Configuració Requerida

Aquesta skill requereix:
1. **Virtualenv activat** amb destral instal·lat. El nom habitual és `erp`:
   - pyenv: `pyenv activate erp`
   - virtualenvwrapper: `workon erp`
2. **Workspace definit** amb els repositoris `erp`, `destral` i `openerp_som_addons`:
   ```bash
   export WORKSPACE=/home/<user>/src
   test -d "$WORKSPACE/erp"
   test -d "$WORKSPACE/destral"
   test -f "$WORKSPACE/openerp_som_addons/docker-compose.yaml"
   ```
3. **Contenidors Docker**: PostgreSQL, MongoDB, Redis

## Workflow

### Pas 1: Verificar Contenidors

```bash
COMPOSE_FILE="$WORKSPACE/openerp_som_addons/docker-compose.yaml"
docker compose -f "$COMPOSE_FILE" ps
```

Serveis esperats:
- `postgres`
- `mongo`
- `redis`

Si no estan actius:
```bash
docker compose -f "$COMPOSE_FILE" up -d postgres mongo redis
```

### Pas 2: Executar tests

En worktrees és obligatori usar `scripts/run-tests-worktree.sh`, declarar cada addon redirigit amb `--addon` i separar els arguments de `run-tests.sh` amb `--`. No executis `run-tests.sh` directament ni modifiquis els symlinks compartits manualment.

```bash
scripts/run-tests-worktree.sh --addon <module_name> -- <database> --no-requirements -m <module_name>
```

Si **no** passes `<database>`, `run-tests.sh` genera una DB determinística per branca/PR i la reutilitza entre execucions:

```bash
scripts/run-tests-worktree.sh --addon <module_name> -- --no-requirements -m <module_name>
```

En aquest mode, `run-tests.sh`, invocat pel wrapper, afegeix `--no-dropdb` automàticament (si no l'has passat tu), perquè la DB es conservi.

**Exemple**:
```bash
scripts/run-tests-worktree.sh --addon <module_name> -- <database> --no-requirements -m <module_name>
```

Test únic:
```bash
scripts/run-tests-worktree.sh --addon <module_name> -- <database> --no-requirements -m <module_name> -t <TestClass.test_method>
```

Forçar DB nova (sense reutilitzar cache de branca/PR):
```bash
OPENERP_TEST_DB_FRESH=1 scripts/run-tests-worktree.sh --addon <module_name> -- --no-requirements -m <module_name>
```

En mode `OPENERP_TEST_DB_FRESH=1`, `run-tests.sh`, invocat pel wrapper, afegeix `--dropdb` automàticament (si no l'has passat tu) per netejar aquesta execució puntual.

Opcionalment pots fixar la referència usada per al nom determinístic:
```bash
OPENERP_TEST_DB_REF="<branch_name>" scripts/run-tests-worktree.sh --addon <module_name> -- --no-requirements -m <module_name>
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| `WORKSPACE no definit` | Falta la ruta arrel del workspace | `export WORKSPACE=/home/<user>/src` |
| `destral: command not found` | Virtualenv no activat | `pyenv activate erp` o `workon erp` |
| `Connection refused to localhost:5432` | PostgreSQL no corrent | `docker compose -f "$WORKSPACE/openerp_som_addons/docker-compose.yaml" up -d postgres` |
| `Connection refused to localhost:27017` | MongoDB no corrent | `docker compose -f "$WORKSPACE/openerp_som_addons/docker-compose.yaml" up -d mongo` |
| `Connection refused to localhost:6379` | Redis no corrent | `docker compose -f "$WORKSPACE/openerp_som_addons/docker-compose.yaml" up -d redis` |
| `Database does not exist` | DB no creada | destral la crea automàticament |
| `timeout` | Tests molt lents | Els tests d'OpenERP poden trigar 10+ min |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-apply`: Per verificar que el codi implementat passa els tests
- `sdd-verify`: Per validar contra specs

El runner obligatori en worktrees és `scripts/run-tests-worktree.sh`; aquest serialitza els symlinks compartits i delega a `scripts/run-tests.sh` mantenint el lock durant Destral.
