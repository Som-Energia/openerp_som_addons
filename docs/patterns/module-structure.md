# Patró: Estructura d'un Mòdul

## Problema

No sabem quines carpetes i fitxers ha de tenir un mòdul i quin és el propòsit de cada un.

## Estructura completa

```
module_name/
├── __init__.py              #① Import del mòdul
├── __terp__.py              #② Meta-informació del mòdul
├── security/                #③ permisos i grups
│   ├── ir.model.access.csv  # Permisos d'accés
│   └── ir.module.category.csv
├── data/                    #④ Dades inicials (no demo)
│   ├── module_data.xml      # Seqüències, valors per defecte
│   └── module_config.xml    # Configuracions
├── demo/                    #⑤ Dades de demo (per tests)
│   └── demo_data.xml        # Dades de prova
├── models/                  #⑥ Models Python
│   ├── __init__.py          # Importar tots els fitxers
│   ├── model_1.py           # Un fitxer per model (o grup de models)
│   └── model_2.py
├── views/                   #⑦ Vistes XML
│   ├── model_1_view.xml     # Form, tree, search
│   └── model_2_view.xml
├── wizard/                   #⑧ Wizards (forms temporals)
│   ├── __init__.py
│   ├── wizard_1.py
│   └── wizard_1_view.xml
├── report/                   #⑨ Reports (Odoo reports antics)
│   ├── __init__.py
│   ├── report_1.py
│   └── report_1.rml         # Plantilles RML/PDF
├── i18n/                     #⑩ Traduccions
│   ├── ca.po                 # Català
│   └── es.po                 # Castellà
└── tests/                    #⑪ Tests
    ├── __init__.py
    ├── test_model_1.py
    └── test_model_2.py
```

## Detall de cada carpeta

### `__init__.py` i `__terp__.py`

```python
# __init__.py
import models
import wizard
import report
```

```python
# __terp__.py
{
    "name": "Module Name",
    "version": "1.0",
    "depends": ["base"],
    "author": "Som Energia",
    "description": """Descripció del mòdul""",
    "init_xml": [],
    "update_xml": [
        "security/ir.model.access.csv",
        "data/module_data.xml",
        "views/model_view.xml",
    ],
    "installable": True,
}
```

### `security/` — Permisos

#### Estructura del fitxer

El fitxer `ir.model.access.csv` segueix el següent format:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
```

#### Models: 3 nivells de permisos

Per a cada **model**, es defineixen 3 grups:

| Grup | Nom | R | W | C | U | Ús |
|------|-----|---|---|---|---|---|
| Read-only | `_r` | 1 | 0 | 0 | 0 | Consultes puntuals |
| User | `_w` | 1 | 1 | 1 | 0 | Usuari estàndard |
| Manager | `_u` | 1 | 1 | 1 | 1 | Administrador |

Exemple per a `model_som_my_model`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_som_my_model_r,som.my.model,model_som_my_model,module_name.group_som_my_model_r,1,0,0,0
access_som_my_model_w,som.my.model,model_som_my_model,module_name.group_som_my_model_w,1,1,1,0
access_som_my_model_u,som.my.model,model_som_my_model,module_name.group_som_my_model_u,1,1,1,1
```

**Nota**: El grup manager (`_u`) només s diferencia de user (`_w`) en el permís `unlink`.

#### Wizards: 1-2 grups

Els wizards normalment tenen 1 o 2 grups, ja que solen ser actions puntuals:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_wizard_my_action_r,wizard.my.action,model_wizard_my_action,module_name.group_my_action_r,1,0,0,0
access_wizard_my_action_u,wizard.my.action,model_wizard_my_action,module_name.group_my_action_u,1,1,1,1
```

#### Grups: creats vs existents

- **Crear grups nous**: Només si és una funcionalitat molt desacoblada
- **Grups existents**: Utilitzar els del projecte quan sigui possible

Exemples de grups existents:
- `base.group_user` — Usuari base d'Odoo
- `base.group_erp_manager` — Administrador ERP
- `crm.group_crm_user`, `crm.group_crm_manager` — CRM
- `giscedata_facturacio.group_giscedata_facturacio_u` — Facturació
- `account.group_account_user`, `account.group_account_manager` — Comptabilitat

#### Definir grups (ir.module.category.csv)

Si cal crear grups nous, primer cal definir la categoria i el grup:

```csv
# security/ir.module.category.csv
id,name,parent:id
module_name.module_category,Module Name,base.module_category_root
```

```csv
# security/res.groups.csv
id,name,category:id,implied_ids:id
module_name.group_module_name_r,My Model Read Only,module_name.module_category,base.group_user
module_name.group_module_name_w,My Model User,module_name.module_category,base.group_user
module_name.group_module_name_u,My Model Manager,module_name.module_category,base.group_user
```

### `data/` — Dades inicials

Dades necessàries perquè el mòdul funcioni:
- Seqüències (`ir.sequence`)
- Valors per defecte
- Configuracions de paràmetres

```xml
<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data>
        <!-- Seqüència -->
        <record id="seq_my_sequence" model="ir.sequence">
            <field name="name">Seqüència demo</field>
            <field name="code">my.sequence.code</field>
            <field name="padding">5</field>
        </record>
    </data>
</openerp>
```

### `demo/` — Dades de demo per tests

Igual que `data/` però **només per a tests**. Utilitza `noupdate="1"`.

### `models/` — Models Python

```python
# models/__init__.py
import giscedata_polissa
import som_my_model
```

```python
# models/som_my_model.py
from osv import osv, fields


class SomMyModel(osv.osv):
    _name = "som.my.model"
    _inherit = "som.my.model"

    _columns = {
        "name": fields.char(u"Nom", size=256),
    }


SomMyModel()
```

#### Canvis a models: scripts de migració

Quan es modifica un model (nou camp, canvi de tipus, etc.), cal crear un script de migració.

Consulta el skill [erp-migration](../../.agents/skills/erp-migration/SKILL.md) per crear scripts de migració automàticament amb `scripts/create_migration_script.py`.

### `views/` — Vistes XML

```xml
<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data>
        <!-- Vista de formulari -->
        <record id="view_som_my_model_form" model="ir.ui.view">
            <field name="name">som.my.model.form</field>
            <field name="model">som.my.model</field>
            <field name="type">form</field>
            <field name="arch" type="xml">
                <form string="Model">
                    <group colspan="4" col="4">
                        <field name="name"/>
                    </group>
                </form>
            </field>
        </record>

        <!-- Action -->
        <record id="action_som_my_model" model="ir.actions.act_window">
            <field name="name">Model</field>
            <field name="res_model">som.my.model</field>
            <field name="view_type">form</field>
            <field name="view_mode">tree,form</field>
        </record>

        <!-- Menú -->
        <menuitem id="menu_som_my_model" parent="menu_parent" action="action_som_my_model"/>
    </data>
</openerp>
```

### `wizard/` — Wizards

```python
# wizard/__init__.py
import wizard_action
```

```python
# wizard/wizard_action.py
from osv import osv, fields


class WizardAction(osv.osv_memory):
    _name = "wizard.action"

    _columns = {
        "name": fields.char(u"Nom", size=256),
    }

    def action_execute(self, cursor, uid, ids, context=None):
        # Fer alguna cosa
        return {"type": "ir.actions.act_window_close"}


WizardAction()
```

### `report/` — Reports

Mòduls antics de reports (abans de Odoo 10). Actualment s'utilitzen altres mètodes.

### `i18n/` — Traduccions

```
i18n/
├── ca.po    # Català
├── es.po    # Castellà
└── en.po    # Anglès
```

```po
# i18n/ca.po
msgid "Name"
msgstr "Nom"
```

### `tests/` — Tests

```python
# tests/__init__.py
from destral import testing
```

```python
# tests/test_som_my_model.py
from destral import testing
from destral.testing import OOTestCase


class TestSomMyModel(OOTestCase):
    def setUp(self):
        self.model = self.openerp.pool.get("som.my.model")

    def test_create(self):
        id = self.model.create(
            self.cursor,
            self.uid,
            {"name": "Test"},
        )
        self.assertTrue(id)
```

## Resum: Quan crear cada carpeta

| Carpeta | Necessària si... |
|---------|------------------|
| `models/` | Sempre que hi hagi models |
| `views/` | Sempre que hi hagi vistes |
| `security/` | Cal configurar accesos a models o wizards |
| `data/` | Cal crear seqüències o configs |
| `demo/` | Cal fer tests |
| `wizard/` | Cal fer assitents i accions sobre models |
| `report/` | Cal generar PDF/reports antics |
| `i18n/` | Cal traduir |
| `tests/` | Cal tests |

**Font:** Mòduls de `openerp_som_addons`, especialment `som_autoreclama/`, `som_polissa/`
