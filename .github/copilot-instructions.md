# Instruccions per a GitHub Copilot
Aquest repositori conté addons per a OpenERP 5.0 utilitzats per Som Energia. Aquestes instruccions defineixen l’estil, arquitectura i criteris que Copilot ha de seguir quan generi codi o documentació.

## Objectiu general
- Generar codi Python i XML compatible amb OpenERP 5.0.
- Respectar l’estil i convencions històriques de Som Energia.
- Prioritzar mantenibilitat i simplicitat, evitant funcionalitats modernes d’Odoo.
- No introduir API, patrons o mòduls que no existeixen a OpenERP 5.

## Estil de programació
- Seguir les guies definides a `.github/docs/estil.md`.
- Python senzill, compatible amb OpenERP 5 (Python 2.7 però comptabile amb Python 3.11).
- Evitar decoradors i API nova (`@api.model`, `@api.depends`, etc.).
- Utilitzar l’ORM antic: `osv.osv`, `osv.osv_memory`, `_columns`, `fields.*`.
- Evitar comprensions complexes, patrons avançats o sintaxi moderna.

## Arquitectura i estructura
- Seguir les directrius de `.github/docs/arquitectura.md`.
- Respectar l’estructura típica d’un mòdul OpenERP 5:
  - `__terp__.py`
  - `__init__.py`
  - `models/`
  - `views/`
  - `wizard/`
  - `report/`
  - `security/`
  - `data/`
  - `i18n/`
  - `tests/`
  - `demo/`
- No crear carpetes noves sense justificació.
- No introduir dependències externes no aprovades.

## Bones pràctiques específiques d’OpenERP 5
- Utilitzar `osv.osv` i `osv.osv_memory` correctament.
- Definir `_columns` amb `fields.char`, `fields.many2one`, etc.
- Utilitzar `_defaults` en lloc de `@api.model`.
- Utilitzar `cursor`, `uid`, `ids`, `context` en tots els mètodes.
- Evitar SQL cru si es pot utilitzar l’ORM antic.
- Evitar sobreescriptures massives de mètodes base.

## Fitxers de suport
Copilot ha de tenir en compte els fitxers següents quan existeixin:

- `.github/docs/estil.md`
- `.github/docs/evitar.md`
- `.github/docs/arquitectura.md`
- `.github/docs/desenvolupament.md`
- `docs/patterns/` — Plantilles de patrons (receptes per a tasques recurrents):
  - `docs/patterns/model-inherit.md` — Com heretar un model
  - `docs/patterns/field-add.md` — Com afegir un camp
  - `docs/patterns/view-extend.md` — Com estendre una vista XML
  - `docs/patterns/wizard.md` — Com crear un wizard
  - `docs/patterns/test-basic.md` — Com escriure tests
  - `docs/patterns/demo-data.md` — Com crear dades demo
  - `docs/patterns/module-structure.md` — Estructura d'un mòdul

## Notes finals
Aquestes instruccions són prioritàries per sobre de qualsevol suggeriment general del model.
