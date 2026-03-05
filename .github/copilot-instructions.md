# Instruccions per a GitHub Copilot
Aquest repositori conté addons per a OpenERP 5.0 utilitzats per Som Energia. Aquestes instruccions defineixen l’estil, arquitectura i criteris que Copilot ha de seguir quan generi codi o documentació.

## Objectiu general
- Generar codi Python i XML compatible amb OpenERP 5.0.
- Respectar l’estil i convencions històriques de Som Energia.
- Prioritzar mantenibilitat i simplicitat, evitant funcionalitats modernes d’Odoo.
- No introduir API, patrons o mòduls que no existeixen a OpenERP 5.

## Estil de programació
- Seguir les guies definides a `/prompts/estil.md`.
- Python senzill, compatible amb OpenERP 5 (Python 2.5/2.6).
- Evitar decoradors i API nova (`@api.model`, `@api.depends`, etc.).
- Utilitzar l’ORM antic: `osv.osv`, `osv.osv_memory`, `_columns`, `fields.*`.
- Evitar comprensions complexes, patrons avançats o sintaxi moderna.

## Arquitectura i estructura
- Seguir les directrius de `/prompts/arquitectura.md`.
- Respectar l’estructura típica d’un mòdul OpenERP 5:
  - `__openerp__.py`
  - `__init__.py`
  - `wizard/`
  - `report/`
  - `security/`
  - `data/`
  - `view/`
  - `i18n/`
- No crear carpetes noves sense justificació.
- No introduir dependències externes no aprovades.

## Bones pràctiques específiques d’OpenERP 5
- Utilitzar `osv.osv` i `osv.osv_memory` correctament.
- Definir `_columns` amb `fields.char`, `fields.many2one`, etc.
- Utilitzar `_defaults` en lloc de `@api.model`.
- Utilitzar `cr`, `uid`, `ids`, `context` en tots els mètodes.
- Evitar SQL cru si es pot utilitzar l’ORM antic.
- Evitar sobreescriptures massives de mètodes base.

## Coses que NO vull que Copilot faci
- No proposar API moderna d’Odoo (8.0+).
- No suggerir frameworks o llibreries alienes a OpenERP 5.
- No generar receptes, exemples irrelevants o contingut no tècnic.
- No suggerir patrons OOP complexos (factory, strategy, etc.).
- No utilitzar sintaxi moderna de Python 3.

## Fitxers de suport
Copilot ha de tenir en compte els fitxers següents quan existeixin:

- `/prompts/estil.md`
- `/prompts/evitar.md`
- `/prompts/arquitectura.md`

## Notes finals
Aquestes instruccions són prioritàries per sobre de qualsevol suggeriment general del model.
