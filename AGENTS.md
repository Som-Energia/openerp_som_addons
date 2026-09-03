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

**PR worktree policy:**
- PR-affecting work must use a named worktree under `<WORKSPACE>/openerp_som_addons-worktrees/`, where `<WORKSPACE>` is the directory containing the primary repository checkout; never use `/tmp/opencode`.
- Announce the active worktree before making edits.
- If no appropriate worktree exists, stop and get explicit approval before creating one.

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `git-branch` | Crear branca nova | Veure [.agents/skills/git-branch/SKILL.md](.agents/skills/git-branch/SKILL.md) |
| `git-commit` | Fer commit | Veure [.agents/skills/git-commit/SKILL.md](.agents/skills/git-commit/SKILL.md) |
| `git-pr` | Crear PR | Veure [.agents/skills/git-pr/SKILL.md](.agents/skills/git-pr/SKILL.md) |

### Current PR Policy

Repository GitHub workflows and repository rules are authoritative for PR requirements. Verify any generic or global skill requirement against them before applying it to this repository.

Currently, `.github/workflows/pull_request_labeler.yml` requires each PR to have at least one label. It does not require an approved linked issue or a `type:*` label. This is the current policy and may change with repository workflows or rules.

### Noms de branca

Utilitza el format `<PREFIX>_<descripcio>`:

- Prefix: `ADD_`, `IMP_`, `FIX_`, `MOD_`, `REF_`, `TEST_`, `DOCS_` o `CI_`.
- Descripció: 2 o 3 paraules en anglès, minúscules i separades per `_`.

Exemple: `IMP_invoice_payment_type_views`.

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

Useu el wrapper del projecte, no un runner de tests manual. Inicieu sempre PostgreSQL, MongoDB i Redis abans dels tests. `$WORKSPACE/erp/server/bin/addons` és estat compartit i mutable: redirigiu temporalment només els enllaços dels addons modificats del worktree (directoris amb `__terp__.py`) i preserveu-ne el destí original.

No modifiqueu aquests enllaços alhora que ERP o tests d'un altre worktree. El manifest temporal extern i el `trap` següents restauren tots els enllaços originals tant si el test acaba bé com si falla o s'interromp:

```bash
WORKTREE="$(git rev-parse --show-toplevel)"
WORKSPACE="$(dirname "$(dirname "$WORKTREE")")"
DATABASE="<database>"
MODULE="<module>"
ADDONS="$WORKSPACE/erp/server/bin/addons"
MANIFEST="$(mktemp)"

restore_links() {
    while IFS=$'\t' read -r link target; do
        rm -f "$link"
        ln -s "$target" "$link"
    done < "$MANIFEST"
    rm -f "$MANIFEST"
}
trap restore_links EXIT INT TERM

docker compose -f "$WORKTREE/docker-compose.yaml" up -d

while IFS= read -r -d '' addon; do
    name="$(basename "$addon")"
    link="$ADDONS/$name"

    if [ -e "$link" ] && [ ! -L "$link" ]; then
        printf 'Refuso substituir %s: no és un enllaç simbòlic.\n' "$link" >&2
        exit 1
    fi
    if [ -L "$link" ]; then
        printf '%s\t%s\n' "$link" "$(readlink "$link")" >> "$MANIFEST"
        rm "$link"
    fi
    ln -s "$addon" "$link"
done < <(find "$WORKTREE" -type f -name __terp__.py -printf '%h\0')

PYENV_VERSION=erp "$WORKTREE/scripts/run-tests.sh" "$DATABASE" --no-requirements -m "$MODULE"
```

En acabar, el `trap` restaura tots els enllaços originals. No executeu canvis d'enllaços d'addons de worktrees concurrentment amb ERP o tests d'un altre worktree.

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
