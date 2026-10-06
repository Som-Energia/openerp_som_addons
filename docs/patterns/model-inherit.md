# Patró: Model Inherit

## Problema

Necessites afegir mètodes o modificacions a un model existent (`giscedata.polissa`, `res.partner`, etc.) sense modificar el mòdul original.

## Solució

1. Crear un fitxer Python dins el mòdul
2. Definir una classe que hereti del model existent
3. Definir `_name` i `_inherit` amb el mateix nom

## Exemple

```python
# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    """Afegim funcionalitat extra a giscedata.polissa."""

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def my_custom_method(self, cursor, uid, ids, context=None):
        # Fer alguna cosa
        return True


GiscedataPolissa()
```

**Font:** `som_autoreclama/models/giscedata_polissa.py`

Tota la resta (camps, mètodes, etc.) s'afegeixen al model original.
