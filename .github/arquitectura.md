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

## Models
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
- Basats en `osv.osv_memory`.
- Flux simple i clar.
- Evitar lògica massa complexa.

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
