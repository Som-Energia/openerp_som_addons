# Instruccions per a Gemini CLI

Treballa amb el repositori `openerp_som_addons`.

## Tech Stack
- OpenERP/OpenERP 7 (Python 2.7)
- Testing: destral
- Linting: flake8

## Skills

Utilitza les skills del projecte quan correspongui. Veure [.agents/skill-registry.md](.agents/skill-registry.md):
- `git-branch`, `git-commit`, `git-pr` - Git workflow
- `erp-test`, `erp-start`, `erp-migration` - ERP operations

## Convencions

### Branques
```
<TYPE>_<description>
```
Types: ADD_, IMP_, FIX_, MOD_, REF_, TEST_

### Commits
```
<emoji> <type>: <description>
```
Tipus: feat, fix, refactor, perf, test, docs, style, chore

## Estil de Codi
- `.github/docs/estil.md`
- `.github/docs/evitar.md`
- Evitar API nova (@api.model, @api.depends)
- Utilitzar `osv.osv`, `_columns`, `fields.*`
