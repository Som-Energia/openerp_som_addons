# Patró: Demo Data per Tests

## Problema

Necessites dades de prova per executar tests sense dependre de l'estat de la base de dades.

## Solució

1. Crear un fitxer XML de dades demo dins `demo/`
2. Carregar-lo als tests amb `load_xml_id`

## Estructura típica

```
module_name/
├── demo/
│   └── my_data.xml
└── tests/
    └── test_module.py
```

## Exemple: XML de demo data

```xml
<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data noupdate="1">
        <!-- Partner de prova -->
        <record id="demo_partner_1" model="res.partner">
            <field name="name">Client Demo</field>
            <field name="vat">ES12345678Z</field>
            <field name="email">demo@example.com</field>
        </record>

        <!-- Polissa de prova -->
        <record id="demo_polissa_1" model="giscedata.polissa">
            <field name="name">1234</field>
            <field name="cups">ES1234000000000001AA0</field>
            <field name="tarifa">tarifae</field>
            <field name="potencia">4500</field>
            <field name="state">actiu</field>
        </record>
    </data>
</openerp>
```

## Carregar als tests

```python
# -*- coding: utf-8 -*-
from destral import testing
from destral.testing import OOTestCase


class TestMyFeature(OOTestCase):
    """Tests pel mòdul."""

    def setUp(self):
        """Carrega les dades demo."""
        # Carregar totes les dades demo del mòdul
        self.load_xml_id("my_module")
        # O carregar un fitxer específic
        # self.load_xml_id("my_module.my_data_file")

    def test_with_partner(self):
        """Test que utilitza el partner demo."""
        partner_model = self.openerp.pool.get("res.partner")
        # Obtenir ID del partner demo
        partner_id = self.refs["demo_partner_1"]
        # O buscar-lo directament
        partner_id = partner_model.search(
            self.cursor,
            self.uid,
            [("vat", "=", "ES12345678Z")],
        )[0]
```

## Exemple: Dades complexes amb relacions

```xml
<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data noupdate="1">
        <!-- Primer crear el partner -->
        <record id="demo_partner_complex" model="res.partner">
            <field name="name">Soci Demo</field>
            <field name="is_soci" eval="True"/>
        </record>

        <!-- Ara crear la pòlissa que referencia el partner -->
        <record id="demo_polissa_complex" model="giscedata.polissa">
            <field name="name">5678</field>
            <field name="cups">ES1234000000000002AA0</field>
            <field name="tarifa">tarifa3a</field>
            <field name="potencia">5500</field>
            <field name="state">actiu</field>
            <field name="soci" ref="demo_partner_complex"/>
        </record>
    </data>
</openerp>
```

## Crear dades directament als tests

 Quan les dades XML no són prou flexibles:

```python
def setUp(self):
    """Crear dades específiques per al test."""
    self.partner_model = self.openerp.pool.get("res.partner")
    self.polissa_model = self.openerp.pool.get("giscedata.polissa")

    # Crear partner
    self.partner_id = self.partner_model.create(
        self.cursor,
        self.uid,
        {
            "name": "Partner Test",
            "vat": "ES99999999R",
        },
    )

    # Crear pòlissa associada
    self.polissa_id = self.polissa_model.create(
        self.cursor,
        self.uid,
        {
            "name": "9999",
            "cups": "ES1234000000009999AA0",
            "tarifa": "tarifae",
            "soci": self.partner_id,
        },
    )
```

## Dades de referència (cross-module)

```python
# Referenciar dades d'altres mòduls
def setUp(self):
    # Carregar mòdul que conté les dades
    self.load_xml_id("som_polissa")
    # Obtenir referència
    polissa_id = self.refs["som_polissa.demo_polissa"]
```

## Noupdate

| Valor | Ús |
|-------|-----|
| `noupdate="1"` | Dades fixes, no es sobreescriuen en actualitzacions |
| `noupdate="0"` | Dades que es poden modificar en actualitzacions |

Per tests, **sempre** utilitzar `noupdate="1"`.

**Font:** `som_autoreclama/tests/test_som_autoreclama_base.py`, `som_polissa_soci/tests/test_somenergia_soci.py`
