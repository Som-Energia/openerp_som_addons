# Patró: Afegir un camp

## Problema

Necessites afegir un camp nou a un model existent (per exemple, `giscedata.polissa`, `res.partner`).

## Solució

1. Crear una classe que hereti del model (vegeu [model-inherit](model-inherit.md))
2. Definir `_columns` amb el camp nou

Els tipus de camps més comuns:
- `char` — Text curt (max 256 caràcters)
- `text` — Text llarg
- `integer` — Enter
- `float` — Decimal
- `boolean` — Sí/No
- `date` — Data
- `datetime` — Data i hora
- `many2one` — Relació N:1
- `one2many` — Relació 1:N
- `many2many` — Relació N:N

## Exemple

```python
# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    """Afegim un camp a giscedata.polissa."""

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    _columns = {
        "x_new_field": fields.char(
            u"Nou camp",
            size=256,
            required=True,
            help=u"Descripció del camp",
        ),
    }


GiscedataPolissa()
```

### Exemple amb many2one

```python
_columns = {
    "x_partner_id": fields.many2one(
        "res.partner",
        u"Client associat",
        required=True,
    ),
}
```

### Exemple amb selection

```python
_columns = {
    "x_estat": fields.selection(
        [
            ("pendent", u"Pendent"),
            ("actiu", u"Actiu"),
            ("cancelat", u"Cancel·lat"),
        ],
        u"Estat",
        required=True,
    ),
}
```

## Camps calculats

```python
def _get_default_value(self, cursor, uid, context=None):
    return "valor per defecte"


_columns = {
    "x_default_field": fields.char(
        u"Valor per defecte",
        size=256,
        readonly=True,
        fnct=_get_default_value,
    ),
}
```

## Camps relacionats

```python
_columns = {
    "x_partner_name": fields.related(
        "partner_id",
        "name",
        type="char",
        string=u"Nom del client",
        readonly=True,
    ),
}
```

**Font:** `som_autoreclama/models/giscedata_polissa.py`, `som_gurb/models/som_gurb_cups.py`
