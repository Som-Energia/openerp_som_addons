# Instruccions per a Claude Code

Treballa amb el repositori `openerp_som_addons`.

## Tech Stack
- OpenERP/OpenERP 7 (Python 2.7)
- Testing: destral
- Linting: flake8

## Convencions

### Branques
Format: `<TYPE>_<description>`
- ADD_ - Nova funcionalitat
- IMP_ - Millora
- FIX_ - Bug fix
- MOD_ - Canvi de comportament
- REF_ - Refactorització
- TEST_ - Tests

### Commits
Format: `<emoji> <type>: <description>`
- feat, fix, refactor, perf, test, docs, style, chore
- Emoji obligatoris
- Descripció en anglès

### PRs
- Plantilla: `pull_request_template.md`
- Totes les seccions obligatòries

## Testing
```bash
pyenv activate erp
dodestral <db> -m <modul>
```

## Estil de Codi
- `.github/docs/estil.md`
- `.github/docs/evitar.md`
- `.github/docs/arquitectura.md`
- Patterns OpenERP 5: `osv.osv`, `_columns`, `fields.*`
- Evitar API nova: `@api.model`, `@api.depends`
