# Patró: Test bàsic

## Problema

Necessites escriure tests per validar el codi dels mòduls.

## Solució

1. Crear `tests/test_modul.py` dins el mòdul
2. Importar `testing` de `destral`
3. Definir classe de test heretant de `testing.OOTestCase`

## Estructura bàsica

```python
# -*- coding: utf-8 -*-
from destral import testing
from destral.testing import OOTestCase
import osv


class TestMyFeature(OOTestCase):
    """Tests pel mòdul."""

    def setUp(self):
        """Inicialitza els tests."""
        self.model = self.openerp.pool.get("my.model")
        # Carregar dades de demo
        self.refs = self.load_xml_id("module.data_file_xml_id")

    def test_my_feature(self):
        """Test que fa alguna cosa."""
        # Crear registre
        id = self.model.create(
            self.cursor,
            self.uid,
            {"name": "Test"},
        )
        # Verificar
        record = self.model.read(
            self.cursor,
            self.uid,
            id,
            ["name"],
        )
        self.assertEqual(record["name"], "Test")
```

## Tipus de test case

| Classe | Ús |
|--------|-----|
| `OOTestCase` | Test bàsic |
| `OOTestCaseWithCursor` | Test amb cursor propi |

Prioritzem tests amb OOTestCaseWithCursor

```python
class TestWithDB(OOTestCaseWithCursor):
    def test_something(self):
        # Cursor propi disponible
        cursor = self.cursor
        uid = self.uid
```

## Assertions més comunes

```python
self.assertTrue(condition)
self.assertFalse(condition)
self.assertEqual(actual, expected)
self.assertNotEqual(actual, expected)
self.assertIn(element, collection)
self.assertIsNone(value)
self.assertIsNotNone(value)
```

## Carregar dades

### Des de XML

```python
# Carregar demo data
self.load_xml_id("module.my_demo_data")
# Obtenir referència
partner_id = self.refs["res_partner_demo"]
```

### Directament

```python
def setUp(self):
    self.partner_model = self.openerp.pool.get("res.partner")
    self.partner_id = self.partner_model.create(
        self.cursor,
        self.uid,
        {"name": "Test Partner"},
    )
```

## Test amb SQL

```python
def test_sql(self):
    self.cursor.execute(
        "SELECT id FROM res_partner WHERE name = %s",
        ("Test Partner",),
    )
    result = self.cursor.fetchone()
    self.assertIsNotNone(result)
```

## Executar els tests

```bash
# Des del directori del projecte
python -m pytest src/destral -- -m test_modul
# O amb make
make test module=som_modul
```

**Fonts:** `som_autoreclama/tests/test_som_autoreclama_base.py`, `som_switching/tests/tests_activaciones.py`
