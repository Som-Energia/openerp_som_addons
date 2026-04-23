# Skill Registry

**Project**: openerp_som_addons
**Generated**: 2026-04-23
**Stack**: Odoo/OpenERP (Python 2.7)

## Available Skills

| Trigger | Skill |
|---------|-------|
| "go-testing", "go test", teatest | go-testing |
| "judgment day", "review adversarial", "dual review" | judgment-day |
| "create skill", "new skill", "add agent instructions" | skill-creator |
| "update skills", "skill registry" | skill-registry |
| "sdd init", "iniciar sdd" | sdd-init |
| "sdd explore", "explorar" | sdd-explore |
| "sdd propose", "proponer cambio" | sdd-propose |
| "sdd spec", "especificar" | sdd-spec |
| "sdd design", "disenar" | sdd-design |
| "sdd tasks", "tareas" | sdd-tasks |
| "sdd apply", "implementar" | sdd-apply |
| "sdd verify", "verificar" | sdd-verify |
| "sdd archive", "archivar" | sdd-archive |
| "sdd onboard", "onboard" | sdd-onboard |
| "branch-pr", "pull request", "create pr" | branch-pr |
| "issue-creation", "create issue", "new issue" | issue-creation |

## Project Conventions

### Tech Stack
- **Framework**: Odoo/OpenERP 7 (Som Energia custom modules)
- **Python**: 2.7 legacy
- **Testing**: destral (OOMigration test framework)
- **Linting**: flake8 + autopep8 + autoflake (pre-commit)

### Code Patterns
- Modular addon structure (~60 modules)
- XML models definition
- Wizard patterns for user flows
- SQL triggers in migrations

### Quality Tools
- **Linter**: flake8, autopep8, autoflake
- **Formatter**: autopep8
- **Type checker**: None
- **CI**: GitHub Actions (per-module workflows)
