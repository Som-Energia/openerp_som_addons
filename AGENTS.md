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
├── som_* /              # Mòduls propis de Som Energia
├── giscedata_* /        # Mòduls de facturació
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
| `.github/docs/` | Decisions d'arquitectura i estil |

## Skills Disponibles

Les skills següents estan disponibles al projecte i s'han d'utilitzar quan correspongui:

### Git Workflow

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `git-branch` | Crear branca nova | `git checkout -b <TYPE>_<description>` |
| `git-commit` | Fer commit | `git commit -m "<emoji> <type>: <description>"` |
| `git-pr` | Crear PR | `gh pr create --title "..." --body "..."` |

**Convencions de branca:**
- `ADD_<desc>` - Nova funcionalitat
- `IMP_<desc>` - Millora
- `FIX_<desc>` - Bug fix
- `MOD_<desc>` - Canvi de comportament
- `REF_<desc>` - Refactorització
- `TEST_<desc>` - Tests
- `DOCS_<desc>` - Documentació

**Format de commit:**
- Emoji + type en anglès: `✨ feat: add user auth`
- Tipus: feat, fix, refactor, perf, test, docs, style, chore

### Testing

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `erp-test` | Executar tests | `scripts/run-tests.sh <db> -m <modul>` |

**Requisits per executar tests:**
1. Docker: PostgreSQL, MongoDB, Redis corrent
2. Virtualenv activat (pyenv, venv, o equivalent)

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

## Documentació

| Carpeta | Contingut |
|---------|-----------|
| `docs/patterns/` | Receptes: com fer tasques concretes |
| `docs/guides/` | Guies: conceptes i configuració |
| `.github/docs/` | Decisions d'arquitectura i estil |
