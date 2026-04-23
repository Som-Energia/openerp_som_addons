# Instruccions per a Gemini CLI

Treballa amb el repositori `openerp_som_addons`.

## Tech Stack
- OpenERP/OpenERP 7 (Python 2.7)
- Testing: destral
- Linting: flake8

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

### Tests
```bash
pyenv activate erp && dodestral <db> -m <modul>
```

## Estil de Codi
- `.github/docs/estil.md`
- `.github/docs/evitar.md`
- Evitar API nova (@api.model, @api.depends)
- Utilitzar `osv.osv`, `_columns`, `fields.*`
