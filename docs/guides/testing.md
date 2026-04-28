# Testing

## Framework

Els tests utilitzen [`destral`](https://github.com/gisce/destral), un framework de tests per a OpenERP.

## Estructura bàsica

```python
from destral import testing
from destral.testing import OOTestCase


class TestMyModule(OOTestCase):
    def setUp(self):
        self.model = self.openerp.pool.get("my.model")
        self.load_xml_id("my_module")

    def test_create(self):
        id = self.model.create(
            self.cursor,
            self.uid,
            {"name": "Test"},
        )
        self.assertTrue(id)
```

## Tipus de test case

| Classe | Ús |
|--------|-----|
| `OOTestCase` | Test bàsic |
| `OOTestCaseWithCursor` | Test amb cursor propi |

## Dades de test

### Demo data

Consulta [docs/patterns/demo-data.md](../patterns/demo-data.md) per crear dades demo.

### Crear dades directament

```python
def setUp(self):
    self.partner_model = self.openerp.pool.get("res.partner")
    self.partner_id = self.partner_model.create(
        self.cursor,
        self.uid,
        {"name": "Test Partner"},
    )
```

## Per saber-ne més

- **Receptes de tests**: [docs/patterns/test-basic.md](../patterns/test-basic.md)
- **Demo data**: [docs/patterns/demo-data.md](../patterns/demo-data.md)
- **Patrons OpenERP**: [docs/patterns/](../patterns/)
