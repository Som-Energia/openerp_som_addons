# Arquitectura dels addons d’OpenERP 5.0 a Som Energia

## Estructura bàsica d’un mòdul
- `__terp__.py`: manifest antic.
- `__init__.py`: importacions de models, wizard, report.
- `wizard/`: wizards basats en `osv.osv_memory`.
- `report/`: informes RML o Python.
- `data/`: dades inicials, categories, seqüències.
- `view/`: vistes XML antigues.
- `i18n/`: traduccions `.po`.

## Models
- Definits amb `osv.osv`.
- `_columns` amb `fields.*`.
- `_defaults` per valors inicials.
- Mètodes amb signatura antiga: `(self, cr, uid, ids, context=None)`.

## Wizards
- Basats en `osv.osv_memory`.
- Flux simple i clar.
- Evitar lògica massa complexa.

## Reports
- RML o Python.
- Evitar dependències modernes.

## Integració amb altres addons
- Utilitzar `depends` al manifest antic.
- No introduir dependències circulars.
- Mantenir coherència amb la resta d’addons de Som Energia.

## Notes
- No migrar estructures a Odoo modern.
- No introduir patrons o estructures alienes a OpenERP 5.
