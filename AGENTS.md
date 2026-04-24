# AGENTS.md — openerp_som_addons

Aquest repositori conté addons per a OpenERP 5.0 utilitzats per Som Energia.

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

## Estil i convencions

- Python compatible amb OpenERP 5 (Python 2.7 però compatible Python 3.11)
- ORM antic: `osv.osv`, `osv.osv_memory`, `_columns`, `fields.*`
- Límit de línia: 100 caràcters
- Passar `flake8` abans de commit

## Estructura típica d'un mòdul

```
module_name/
├── __init__.py
├── __terp__.py
├── models/
├── views/
├── wizard/
├── report/
├── security/
├── data/
├── i18n/
├── tests/
└── demo/
```

## Documentació adicional

- `.github/copilot-instructions.md` — Instruccions per a GitHub Copilot
- `.github/docs/` — Documents d'estil, arquitectura i bones pràctiques
