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

Per executar tots els tests d'ERP, primer inicieu totes les dependències amb l'ordre Compose anterior. `WORKSPACE` és l'arrel que conté els repositoris germans `erp`, `destral` i d'addons. Des de dins del worktree d'addons, manteniu l'addon del worktree abans que el checkout d'ERP; en cas contrari, `som_card_payment` es resoldrà des del directori d'addons d'ERP, no des del worktree.

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
: "${WORKSPACE:?Set WORKSPACE to the root containing erp, destral, and addons repositories}"
for path in "$WORKSPACE" "$WORKSPACE/erp/server/bin" "$WORKSPACE/erp/server/bin/addons" "$WORKSPACE/erp/server/sitecustomize" "$WORKSPACE/destral/destral/cli.py"; do
  [ -e "$path" ] || { printf 'Missing required workspace path: %s\n' "$path" >&2; exit 1; }
done
```

Des del worktree, verifiqueu la resolució del codi font abans d'una execució llarga:

```bash
PYTHONPATH="$REPO_ROOT:$WORKSPACE/erp/server/bin:$WORKSPACE/erp/server/bin/addons:$WORKSPACE/erp/server/sitecustomize${PYTHONPATH:+:$PYTHONPATH}" \
  python -c 'import som_card_payment; print(som_card_payment.__file__)'
```

Ha d'imprimir una ruta dins del worktree. A continuació, utilitzeu Destral directament; substituïu els marcadors segons calgui:

```bash
PYENV_VERSION=erp \
PYTHONPATH="$REPO_ROOT:$WORKSPACE/erp/server/bin:$WORKSPACE/erp/server/bin/addons:$WORKSPACE/erp/server/sitecustomize${PYTHONPATH:+:$PYTHONPATH}" \
OPENERP_ADDONS_PATH="$REPO_ROOT" \
OPENERP_ROOT_PATH="$WORKSPACE/erp/server/bin" \
python "$WORKSPACE/destral/destral/cli.py" <database> --no-requirements -m <module> -t <test>
```

Alguns addons esperen `../model_templates`. Si no existeix, creeu l'enllaç simbòlic extern al directori de plantilles d'ERP:

```bash
[ -e "$REPO_ROOT/../model_templates" ] || \
  ln -s "$WORKSPACE/erp/server/bin/model_templates" "$REPO_ROOT/../model_templates"
```

Aquest enllaç simbòlic és una configuració externa de l'entorn, no està versionada i no s'ha de fer commit. `scripts/run-tests.sh` assumeix que el checkout principal d'addons és a `$WORKSPACE/openerp_som_addons`; utilitzeu Destral directament per a un worktree separat, tret que el runner passi a ser compatible amb worktrees.

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
