# AGENTS.md - Instruccions per a Agents IA

Aquest fitxer conté les instruccions i convencions que qualsevol agent IA ha de seguir quan treballi amb el repositori `openerp_som_addons`.

## Tech Stack

- **Framework**: OpenERP v5 (Som Energia custom modules)
- **Python**: 2.7 (compatible amb Python 3)
- **Testing**: destral (OOMigration test framework)
- **Linting**: flake8, autopep8, autoflake (via pre-commit)

## Estructura del Projecte

```
openerp_som_addons/
├── som_* /              # Mòduls propis de Som Energia i herència d'alguns de gisce/erp
├── giscedata_* /        # Mòduls de GISCE que fem herència
├── account_* /          # Mòduls comptables
└── .github/
    ├── workflows/       # CI (schedule_tests_*.yml)
    ├── docs/           # Documentació interna
    └── copilot-instructions.md
```

## Documentació del projecte

| Carpeta | Contingut |
|---------|-----------|
| `docs/patterns/` | Receptes: com fer tasques concretes |
| `docs/guides/` | Guies: conceptes i configuració |
| `docs/guides/sentry-triage-workflow.md` | Workflow per triar repo, issue i PR quan una incidència ve de Sentry |
| `.github/docs/` | Decisions d'arquitectura i estil |

## Skills Disponibles

Les skills següents estan disponibles al projecte i s'han d'utilitzar quan correspongui. Veure [.agents/skill-registry.md](.agents/skill-registry.md) per la llista completa.

### Git Workflow

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `git-branch` | Crear branca nova | Veure [.agents/skills/git-branch/SKILL.md](.agents/skills/git-branch/SKILL.md) |
| `git-commit` | Fer commit | Veure [.agents/skills/git-commit/SKILL.md](.agents/skills/git-commit/SKILL.md) |
| `git-pr` | Crear PR | Veure [.agents/skills/git-pr/SKILL.md](.agents/skills/git-pr/SKILL.md) |

**Convencions de branca:**
- `ADD_<desc>` - Nova funcionalitat
- `IMP_<desc>` - Millora
- `FIX_<desc>` - Bug fix
- `MOD_<desc>` - Canvi de comportament
- `REF_<desc>` - Refactorització
- `TEST_<desc>` - Tests
- `DOCS_<desc>` - Documentació

**Format de commit:**
- Només emoji + descripció en anglès: `✨ add user auth`
- No afegir `feat:`, `fix:` ni cap altre type textual
- Feu els commits amb el virtualenv ERP actiu: els hooks de pre-commit requereixen l'executable `python`. Exemple portable: `PYENV_VERSION=erp git commit -m "✨ add user auth"`.

### Testing

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `erp-test` | Executar tests | Veure [.agents/skills/erp-test/SKILL.md](.agents/skills/erp-test/SKILL.md) |
| `erp-start` | Arrencar servei ERP | Veure [.agents/skills/erp-start/SKILL.md](.agents/skills/erp-start/SKILL.md) |
| `erp-migration` | Crear scripts de migració | Veure [.agents/skills/erp-migration/SKILL.md](.agents/skills/erp-migration/SKILL.md) |
| `erp-demo-testcase` | Crear casos demo XML de test | Veure [.agents/skills/erp-demo-testcase/SKILL.md](.agents/skills/erp-demo-testcase/SKILL.md) |

### Sentry

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `sentry-triage` | Fer triage d'incidències de Sentry | Veure [.agents/skills/sentry-triage/SKILL.md](.agents/skills/sentry-triage/SKILL.md) |

### Reports legals i contractuals

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `update-contract-report` | Actualitzar un report `.mako` legal/contractual a partir d'un `docx` o `md` | Veure [.agents/skills/update-contract-report/SKILL.md](.agents/skills/update-contract-report/SKILL.md) |

**Requisits de l'entorn de tests:**
1. Inicieu els serveis necessaris de PostgreSQL, MongoDB i Redis:
   ```bash
   REPO_ROOT="$(git rev-parse --show-toplevel)"
   docker compose -f "$REPO_ROOT/docker-compose.yaml" up -d
   ```
   Inicieu sempre els tres serveis abans d'executar tests.
2. Virtualenv activat — nom habitual: `erp` (`pyenv activate erp` o `workon erp`)

### Tests en worktrees

Per executar tests des d'un worktree, primer inicieu sempre els tres serveis: PostgreSQL, MongoDB i Redis, amb l'ordre Compose anterior. `link_addons.py` reconstrueix tots els enllaços simbòlics de `$ERP/server/bin/addons`; és estat d'execució compartit i mutable. No l'executeu simultàniament amb una sessió d'ERP, Docker o un altre worktree.

El linker requereix que el checkout font tingui el nom base `openerp_som_addons`. No substituïu l'entrada principal `$WORKSPACE/openerp_som_addons`: creeu un espai de treball temporal separat dins de `$WORKSPACE`, que exposi el worktree amb aquest nom.

```bash
WORKTREE="$(git rev-parse --show-toplevel)"
WORKSPACE="$(dirname "$(dirname "$WORKTREE")")"
ERP="$WORKSPACE/erp"
LINK_WORKSPACE="$WORKSPACE/.worktree-link-pr-1333"

mkdir -p "$LINK_WORKSPACE"
ln -s "$WORKTREE" "$LINK_WORKSPACE/openerp_som_addons"
PYENV_VERSION=erp python "$ERP/tools/link_addons.py" --skip-relative --base-path "$LINK_WORKSPACE"
```

No creeu enllaços simbòlics individuals per addon, recurs o `model_templates`: useu el linker per a tots els camins de mòduls. Després d'executar-lo, el directori `$ERP/server/bin/addons` resol els addons del worktree i els addons restants configurats pel linker.

Des del worktree, exporteu el contracte complet de `scripts/run-tests.sh`, amb el worktree primer només al `PYTHONPATH`. `$WORKSPACE/oorq` és una dependència local del runtime ERP, no un paquet de `pip`, i ha d'anar abans que Python resolgui `oorq.tasks`. Els tres directoris d'ERP són necessaris: `osv` viu a `server/bin`, mentre que els addons base viuen a `server/bin/addons`. Manteniu `OPENERP_ADDONS_PATH` a `$ERP/server/bin/addons`, no a l'arrel del worktree: `link_addons.py` selecciona les substitucions del worktree mitjançant els enllaços simbòlics d'aquest directori.

```bash
WORKTREE="$(git rev-parse --show-toplevel)"
WORKSPACE="$(dirname "$(dirname "$WORKTREE")")"
ERP="$WORKSPACE/erp"

export PYTHONIOENCODING="UTF-8"
export PYTHONUNBUFFERED="1"
export PYTHONPATH="$WORKTREE:$WORKSPACE/oorq:$ERP/server/bin:$ERP/server/bin/addons:$ERP/server/sitecustomize:${PYTHONPATH:-}"
export DEBUG_ENABLED=0
export OORQ_ASYNC=0
export DESTRAL_TESTING_LANGS="['en_US','ca_ES','es_ES']"
export OPENERP_ADDONS_PATH="$ERP/server/bin/addons"
export OPENERP_DB_HOST="localhost"
export OPENERP_DB_PORT="5432"
export OPENERP_DB_USER="erp"
export OPENERP_DB_PASSWORD="erp"
export OPENERP_OORQ_ASYNC="False"
export OPENERP_PRICE_ACCURACY=6
export OPENERP_SECRET="verysecret"
export OPENERP_ROOT_PATH="$ERP/server/bin/"
export OPENERP_REDIS_URL="redis://localhost"
export redis_url="redis://localhost"
export OPENERP_MONGODB_HOST="localhost"
export OPENERP_RUN_SCRIPTS_INTERACTIVE_RESULT=skip
export OPENERP_ENVIRONMENT=local
export OPENERP_SII_TEST_MODE=1
export OPENERP_IGNORE_PUBSUB=1
unset OPENERP_CONFIG OPENERP_SERVER
```

`OPENERP_REDIS_URL` descriu la connexió Redis per al contracte de l'entorn, però el runtime d'OpenERP carregat per Destral consumeix la clau de configuració `redis_url`. Cal exportar ambdues variables amb `redis://localhost`; `REDIS_HOST` i `REDIS_PORT` no substitueixen `redis_url` i provoquen `redis_url not specified` durant la inicialització de la base de dades.

El PostgreSQL local de Compose escolta a `localhost:5432` amb l'usuari `erp` i la contrasenya `erp`. Exporteu aquestes quatre variables `OPENERP_DB_*` i executeu `unset OPENERP_CONFIG OPENERP_SERVER` en el mateix procés que invoca Destral; si no, OpenERP pot ignorar l'entorn o aplicar la configuració heretada i usar l'usuari del sistema operatiu.

Abans d'una execució llarga, executeu aquestes probes ràpides:

```bash
MODULE=MODULE  # Substituïu MODULE pel mòdul sota prova
test -d "$WORKSPACE/oorq"
test -f "$WORKSPACE/oorq/oorq/tasks.py"
PYENV_VERSION=erp python -c 'from osv import osv; print(osv.__file__)'
PYENV_VERSION=erp python -c 'from oorq import tasks; print(tasks.__file__)'
PYENV_VERSION=erp python -c "module = __import__('$MODULE'); print(module.__file__)"
```

Les dues primeres comprovacions han de trobar el checkout local d'`oorq` i el seu fitxer `oorq/tasks.py`. La tercera ha d'imprimir una ruta dins de `$WORKSPACE/erp/server/bin/osv`; la quarta, una ruta dins de `$WORKSPACE/oorq/oorq/tasks.py`; i la cinquena, una ruta dins del worktree per al mòdul indicat a `MODULE`. Si la comprovació d'`osv` falla amb `ImportError: No module named osv.osv`, reviseu `PYTHONPATH`: no useu `$WORKSPACE/erp/...`; l'arrel correcta d'OpenERP v5 és `$WORKSPACE/erp/server/bin`.

A continuació, utilitzeu Destral directament només després que `link_addons.py` hagi apuntat els enllaços d'ERP al worktree. Això replica el contracte del runner, però evita que `scripts/run-tests.sh` usi el checkout principal d'addons. Substituïu els marcadors segons calgui:

```bash
PYENV_VERSION=erp python "$WORKSPACE/destral/destral/cli.py" "$DATABASE" --no-requirements -m "$MODULE" -t "$TEST"
```

En acabar, restaureu els enllaços del checkout principal i elimineu l'espai temporal. Feu-ho només quan no hi hagi cap altra sessió d'ERP, Docker o worktree utilitzant aquests enllaços compartits:

```bash
PYENV_VERSION=erp python "$ERP/tools/link_addons.py"
rm -rf "$LINK_WORKSPACE"
```

`scripts/run-tests.sh` assumeix que el checkout principal d'addons és a `$WORKSPACE/openerp_som_addons`; utilitzeu Destral directament per a un worktree separat, tret que el runner passi a ser compatible amb worktrees.

## Estil de Programació

Seguir `.github/docs/estil.md` i `.github/docs/evitar.md`.

### Patterns d'OpenERP 5

- Utilitzar `osv.osv`, `osv.osv_memory`
- Definir camps amb `_columns` i `fields.*`
- Evitar `@api.model`, `@api.depends` (API nova)
- Mètodes: `def method(self, cursor, uid, ids, context=None):`

## SDD (Spec-Driven Development)

El projecte utilitza SDD per gestionar canvis:

| Fase | Descripció |
|------|------------|
| `sdd-explore` | Investigar i entendre |
| `sdd-propose` | Crear proposta |
| `sdd-spec` | Escriure especificacions |
| `sdd-design` | Disseny tècnic |
| `sdd-tasks` | Dividir en tasques |
| `sdd-apply` | Implementar |
| `sdd-verify` | Verificar contra specs |
| `sdd-archive` | Archivar canvi |

## Comprovacions obligatòries

Abans de crear PR, verificar:
- [ ] Tests passen (`erp-test`)
- [ ] Linting passen (`flake8 .`)
- [ ] S'ha seguit l'estil de codi
