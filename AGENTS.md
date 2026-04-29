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
- Emoji + type en anglès: `✨ feat: add user auth`
- Tipus: feat, fix, refactor, perf, test, docs, style, chore

### Testing

| Skill | Quan usar | Com usar |
|-------|-----------|----------|
| `erp-test` | Executar tests | Veure [.agents/skills/erp-test/SKILL.md](.agents/skills/erp-test/SKILL.md) |
| `erp-start` | Arrencar servei ERP | Veure [.agents/skills/erp-start/SKILL.md](.agents/skills/erp-start/SKILL.md) |
| `erp-migration` | Crear scripts de migració | Veure [.agents/skills/erp-migration/SKILL.md](.agents/skills/erp-migration/SKILL.md) |

**Requisits per executar tests:**
1. Docker: PostgreSQL, MongoDB, Redis corrent
2. Virtualenv activat — nom habitual: `erp` (`pyenv activate erp` o `workon erp`)

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
