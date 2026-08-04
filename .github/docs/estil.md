# Estil de programació per a Som Energia (OpenERP 5.0)

> Veure [docs/guides/getting-started.md](../../docs/guides/getting-started.md) per a la configuració de l'entorn de desenvolupament.

## Python
- Compatible amb Python 2.7 i Python 3.11.
- No utilitzar sintaxi moderna (f-strings, comprehensions complexes, decorators).
- Indentació amb 4 espais.
- Noms de variables descriptius i consistents.
- Evitar funcions massa llargues.

## ORM antic d’OpenERP 5
- Utilitzar `osv.osv` i `osv.osv_memory`.
- Definir `_name`, `_description`, `_columns`, `_defaults`.
- Utilitzar `cursor`, `uid`, `ids`, `context` en tots els mètodes.
- Evitar decoradors (`@api.*`) perquè no existeixen.

## XML
- Utilitzar vistes antigues (`form`, `tree`, `search`).
- Evitar atributs moderns d’Odoo.
- Mantenir l’estil coherent amb la resta d’addons del repositori.
- Indentació amb 4 espais als fitxers XML.

## Estil general
- Codi clar i llegible.
- Comentaris quan calgui, però sense excessos.
- Prioritzar mantenibilitat per sobre d’elegància.
