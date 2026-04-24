# AGENTS.md - Instruccions per a Agents IA

Aquest fitxer conté les instruccions i convencions que qualsevol agent IA ha de seguir quan treballi amb el repositori `openerp_som_addons`.

## Tech Stack

- **Framework**: OpenERP/OERP 7 (Som Energia custom modules)
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

## Patrons i plantilles

Quan treballis amb OpenERP/Odoo en aquest repositori, consulta les plantilles a `docs/patterns/`:

| Patró | Descripció |
|------|-----------|
| [model-inherit](docs/patterns/model-inherit.md) | Com heretar un model existent |
| [field-add](docs/patterns/field-add.md) | Com afegir un camp nou |
| [view-extend](docs/patterns/view-extend.md) | Com estendre una vista XML |
| [wizard](docs/patterns/wizard.md) | Com crear un wizard |
| [test-basic](docs/patterns/test-basic.md) | Com escriure un test |
| [demo-data](docs/patterns/demo-data.md) | Com crear dades demo per tests |
| [module-structure](docs/patterns/module-structure.md) | Estructura d'un mòdul (carpetes i propòsit) |

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
| `erp-test` | Executar tests | `dodestral <db> -m <modul>` |

**Requisits per executar tests:**
1. Docker: PostgreSQL, MongoDB, Redis corrent
2. pyenv: `pyenv activate erp`
3. OpenERP instal·lat a `/home/oriol/somenergia/src/erp/server/bin`

## Estil de Programació

Seguir `.github/docs/estil.md` i `.github/docs/evitar.md`.

### Patterns d'OpenERP 5/OERP 7

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

## Fitxers de Referència

- `.github/docs/estil.md` - Estil de codi
- `.github/docs/evitar.md` - Evitar certs patrons
- `.github/docs/arquitectura.md` - Arquitectura
- `.github/docs/desenvolupament.md` - Desenvolupament
- `pull_request_template.md` - Plantilla de PR
- `docs/patterns/` - Plantilles de patrons
