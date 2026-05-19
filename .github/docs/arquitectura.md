# Arquitectura dels addons d’OpenERP 5.0 a Som Energia

## Estructura bàsica d’un mòdul
- `__terp__.py`: manifest del mòdul.
- `__init__.py`: importacions de models, wizard, report.
- `models/`: definicions de models (`osv.osv`).
- `views/`: vistes XML.
- `wizard/`: wizards basats en `osv.osv_memory`.
- `report/`: informes RML o Python.
- `data/`: dades inicials, categories, seqüències.
- `security/`: control d’accés (`ir.model.access.csv`).
- `migrations/`: scripts de migració per versió.
- `i18n/`: traduccions `.po`.
- `tests/`: carpeta amb els fitxers de tests.
- `demo/`: fitxers de demo data pels tests.

## Models

> Veure [docs/patterns/model-inherit.md](../../docs/patterns/model-inherit.md) per exemples detallats.

- Definits amb `osv.osv`.
- `_columns` amb `fields.*`.
- `_defaults` per valors inicials.
- Mètodes amb signatura antiga: `(self, cursor, uid, ids, context=None)`.
- Accés a altres models via `self.pool.get("model.name")`.

## Camps funcionals

Els camps calculats s’implementen amb `fields.function`:

```python
def _get_total(self, cursor, uid, ids, field_name, arg, context=None):
    res = {}
    for record in self.browse(cursor, uid, ids, context=context):
        res[record.id] = record.qty * record.price
    return res

_columns = {
    "total": fields.function(
        _get_total,
        type="float",
        string="Total",
        store=True,
    ),
}
```

Per calcular múltiples camps en una sola passada, usar `multi=`:

```python
def _get_totals(self, cursor, uid, ids, field_names, arg, context=None):
    res = {}
    for record in self.browse(cursor, uid, ids, context=context):
        res[record.id] = {
            "total_net": record.qty * record.price,
            "total_tax": record.qty * record.price * record.tax,
        }
    return res

_columns = {
    "total_net": fields.function(_get_totals, type="float", string="Net", multi="totals"),
    "total_tax": fields.function(_get_totals, type="float", string="Tax", multi="totals"),
}
```

## Camps relacionals i dominis

```python
_columns = {
    # Many2one
    "partner_id": fields.many2one("res.partner", "Partner", required=True),
    # One2many (invers del many2one)
    "line_ids": fields.one2many("sale.order.line", "order_id", "Lines"),
    # Many2many
    "tag_ids": fields.many2many("res.partner.category", "rel_table", "left_id", "right_id", "Tags"),
}
```

Els camps `fields.related` exposen un camp d'un model relacionat de forma directa, sense haver d'escriure una funció:

```python
_columns = {
    # Accedeix a partner_id.name sense funció manual
    "partner_name": fields.related(
        "partner_id", "name",
        type="char",
        string="Partner Name",
        readonly=True,
    ),
    # Pot navegar múltiples nivells
    "country_id": fields.related(
        "partner_id", "country_id",
        type="many2one",
        relation="res.country",
        string="Country",
        readonly=True,
    ),
}
```

Amb `store=True` el valor es desa a la base de dades i és cercable:

```python
"partner_name": fields.related(
    "partner_id", "name",
    type="char",
    string="Partner Name",
    readonly=True,
    store=True,
),
```

Els dominis de cerca segueixen el format `[(camp, operador, valor)]`:

```python
ids = obj.search(cursor, uid, [
    ("partner_id", "=", partner_id),
    ("state", "not in", ["cancel", "draft"]),
])
```

## Vistes XML i herència

> Veure [docs/patterns/view-extend.md](../../docs/patterns/view-extend.md) per exemples detallats d'herència de vistes.

Definició bàsica:

```xml
<record id="view_mymodel_form" model="ir.ui.view">
    <field name="name">mymodel.form</field>
    <field name="model">my.model</field>
    <field name="type">form</field>
    <field name="arch" type="xml">
        <form string="My Model">
            <field name="name"/>
            <field name="partner_id"/>
        </form>
    </field>
</record>
```

Herència de vistes existents:

```xml
<record id="view_mymodel_form_inherit" model="ir.ui.view">
    <field name="name">mymodel.form.inherit</field>
    <field name="model">my.model</field>
    <field name="type">form</field>
    <field name="inherit_id" ref="base_module.view_mymodel_form"/>
    <field name="arch" type="xml">
        <field name="name" position="after">
            <field name="new_field"/>
        </field>
    </field>
</record>
```

Posicions disponibles: `after`, `before`, `inside`, `replace`.

Els fitxers de vistes s’han de declarar a `update_xml` del `__terp__.py`:

```python
"update_xml": [
    "views/mymodel_views.xml",
],
```

## Wizards

> Veure [docs/patterns/wizard.md](../../docs/patterns/wizard.md) per exemples detallats.

Els wizards hereten de `osv.osv_memory` (les dades no es persisten a la BD un cop tancat).

### Wizard simple

```python
class WizardMyAction(osv.osv_memory):
    _name = "wizard.my.action"

    _columns = {
        "name": fields.char("Name", size=64, required=True),
    }

    def action_confirm(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        wiz = self.browse(cursor, uid, ids[0], context=context)
        # lògica aquí...
        return True

WizardMyAction()
```

Vista i acció per obrir-lo com a popup:

```xml
<record id="view_wizard_my_action_form" model="ir.ui.view">
    <field name="name">wizard.my.action.form</field>
    <field name="model">wizard.my.action</field>
    <field name="type">form</field>
    <field name="arch" type="xml">
        <form string="My Action">
            <field name="name"/>
            <group colspan="4">
                <button special="cancel" string="Cancel·lar" icon="gtk-no" colspan="1"/>
                <button name="action_confirm" string="Confirmar" type="object" icon="gtk-ok" primary="1" colspan="1"/>
            </group>
        </form>
    </field>
</record>

<record id="action_wizard_my_action" model="ir.actions.act_window">
    <field name="name">My Action</field>
    <field name="type">ir.actions.act_window</field>
    <field name="res_model">wizard.my.action</field>
    <field name="view_type">form</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>
</record>
```

### Wizard paginated (multi-pas)

El patró per a wizards amb passos és un camp `state` de tipus `selection` que controla quina secció es mostra. La vista usa `attrs` amb `invisible` per amagar/mostrar grups segons l'estat. Cada botó crida un mètode que escriu el nou estat.

**Model:**

```python
class WizardMultiStep(osv.osv_memory):
    _name = "wizard.multi.step"

    def _state(self, cursor, uid, context=None):
        return [
            ("step1", "Pas 1"),
            ("res_step1", "Resultat pas 1"),
            ("step2", "Pas 2"),
            ("done", "Fet"),
        ]

    _columns = {
        "state": fields.selection(_state, "Estat"),
        "log": fields.text("Log", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "step1",
    }

    def action_step1(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        wiz = self.browse(cursor, uid, ids[0], context=context)
        # processar pas 1...
        wiz.write({"state": "res_step1", "log": "Pas 1 completat"})
        return True

    def go_to_step2(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0])
        wiz.write({"state": "step2"})
        return True

    def action_step2(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0])
        # processar pas 2...
        wiz.write({"state": "done"})
        return True

WizardMultiStep()
```

**Vista:** cada pas és un `<group>` amb `attrs="{'invisible': [('state', '!=', 'step1')]}"`. El camp `state` amb `widget="steps"` mostra una barra de progrés visual dels passos.

```xml
<form string="Multi Step Wizard">
    <field name="state" widget="steps"/>

    <group attrs="{'invisible': [('state', '!=', 'step1')]}">
        <!-- contingut del pas 1 -->
        <group colspan="4">
            <button special="cancel" string="Cancel·lar" icon="gtk-no" colspan="1"/>
            <button name="action_step1" string="Executar" type="object" primary="1" colspan="1"/>
        </group>
    </group>

    <group attrs="{'invisible': [('state', '!=', 'res_step1')]}">
        <!-- resultat del pas 1 -->
        <field name="log" nolabel="1" colspan="4" readonly="1"/>
        <group colspan="4">
            <button special="cancel" string="Tancar" icon="gtk-no" colspan="1"/>
            <button name="go_to_step2" string="Següent" type="object" primary="1" colspan="1" icon="arrow-right"/>
        </group>
    </group>

    <group attrs="{'invisible': [('state', '!=', 'step2')]}">
        <!-- contingut del pas 2 -->
        <group colspan="4">
            <button special="cancel" string="Cancel·lar" icon="gtk-no" colspan="1"/>
            <button name="action_step2" string="Finalitzar" type="object" primary="1" colspan="1"/>
        </group>
    </group>

    <group attrs="{'invisible': [('state', '!=', 'done')]}">
        <!-- resultat final -->
        <group colspan="4">
            <button special="cancel" string="Tancar" icon="gtk-no" colspan="4"/>
        </group>
    </group>
</form>
```

## Reports
- RML o Python.
- Evitar dependències modernes.

## Integració amb altres addons
- Utilitzar `depends` al manifest.
- No introduir dependències circulars.
- Mantenir coherència amb la resta d’addons de Som Energia.

## Notes
- No migrar estructures a Odoo modern.
- No introduir patrons o estructures alienes a OpenERP 5.
