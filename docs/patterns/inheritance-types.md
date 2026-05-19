# Patró: Tipus d'Herència d'OpenERP

## Resum

OpenERP (versió 5) ofereix tres tipus d'herència per extensibilitat de models:

| Tipus | Atrbut | Crea nova taula? | Accés a mètodes pare? |
|-------|--------|-----------------|---------------------|
| Class Inheritance | `_inherit` (mateix `_name`) | ❌ | ✅ |
| Prototyping Inheritance | `_inherit` (diferent `_name`) | ✅ | ✅ |
| Delegation Inheritance | `_inherits` | ✅ | ❌ |

---

## 1. Class Inheritance (Extensió)

### Quan fer-la servir

Per afegir camps, mètodes o modificar el comportament d'un model **sense crear una taula nova**.

### Com fer-la

```python
from osv import osv, fields

class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"  # Mateix nom
    _inherit = "giscedata.polissa"  # Hereta del model original

    def my_custom_method(self, cursor, uid, ids, context=None):
        # Accedim a tots els mètodes originals
        return True

GiscedataPolissa()
```

**Resultat:** No es crea cap taula nova. Els camps i mètodes s'afegeixen al model original.

**Exemple real:** `som_autoreclama/models/giscedata_polissa.py`

---

## 2. Prototyping Inheritance (Clonació)

### Quan fer-la servir

Per crear un model nou que **copi el comportament** de l'original però amb dades independents.

### Com fer-la

```python
from osv import osv, fields

class ClasseVehicle(osv.osv):
    _name = "classe.vehicle"
    _columns = {
        'matricula': fields.char("Matrícula", size=10),
    }

class ClasseVehicleHeredada(osv.osv):
    _name = "classe.vehicle.heredada"  # Nom diferent!
    _inherit = "classe.vehicle"  # Copia estructura i mètodes

ClasseVehicleHeredada()
```

**Resultat:**
- Es crea una **nova taula** `classe_vehicle_heredada`
- Es copien els camps de la taula pare
- Els registres de les dues taules són **independents**

---

## 3. Delegation Inheritance (Composició)

### Quan fer-la fer

Per crear un model que **vincoli** els seus registres a uns d'existents, sense duplicar dades.

### Com fer-la (sense accés a mètodes)

```python
from osv import osv, fields
from collections import OrderedDict

class ClasseVehicle(osv.osv):
    _name = "classe.vehicle"
    _columns = {
        'matricula': fields.char("Matrícula", size=10, required=True),
    }

# Sense osv.OsvInherits -> NO es pot accedir als mètodes pare
class ClasseVehicleHeredada(osv.osv):
    _name = "classe.vehicle.heredada"
    _inherits = OrderedDict([('classe.vehicle', 'matricula')])
    _columns = {
        'matricula': fields.many2one('classe.vehicle', 'Matrícula', required=True),
    }

ClasseVehicleHeredada()
```

**Resultat:**
- Es crea una **nova taula** amb camps propis
- Els registres tenen una **relació 1:1** amb la taula pare (via `matricula`)
- No es pot accedir als mètodes del model pare

### Com fer-la (AMB accés a mètodes)

```python
from osv import osv, osv as OsvInherits, fields
from collections import OrderedDict

class ClasseVehicleHeredada(osv.OsvInherits):  # OsvInherits!
    _name = "classe.vehicle.heredada"
    _inherits = OrderedDict([('classe.vehicle', 'matricula')])
    _columns = {
        'matricula': fields.many2one('classe.vehicle', 'Matrícula', required=True),
    }

ClasseVehicleHeredada()
```

Ara **sí** es pot accedir als mètodes del model pare.

---

## Quan fer servir cada tipus

| Cas d'ús | Tipus recomanat |
|----------|----------------|
| Afegir camps/mètodes a `giscedata.polissa` | **Class Inheritance** |
| Crear un model propi basat en un existent | **Prototyping** |
| Tenir registres vinculats a un model existent | **Delegation** |

---

## Errors comuns

- **Class Inheritance amb diferent `_name`:** S'acaba comportant com Prototyping accidentalment
- **Delegation sense `osv.OsvInherits`:** No es poden cridar mètodes del pare
- **`_inherits` vs `_inherit`:** Confus frequüent — `_inherits` és per delegació, `_inherit` per herència

---

## Enllaços

- [OpenERP Docs: Object Inheritance](https://openerp-server.readthedocs.io/en/latest/03_module_dev_02.html)
- [Model Inherit](model-inherit.md)
- [Afegir Camp](field-add.md)
- [Extendre Vista](view-extend.md)
