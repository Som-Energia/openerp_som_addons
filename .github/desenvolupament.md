# Guia de desenvolupament per a Som Energia (OpenERP 5.0)

## Execució de testos

Els testos utilitzen [`destral`](https://github.com/gisce/destral) i requereixen una instal·lació local de l'ERP i una base de dades de test pre-existent.

```bash
# Tots els testos d'un mòdul
python <ruta_destral>/destral/cli.py --no-requirements -m <nom_modul>

# Un test concret
python <ruta_destral>/destral/cli.py --no-requirements -m <nom_modul> -t TestsClassName.test_method_name
```

Variables d'entorn necessàries (valors d'exemple):
```bash
export OORQ_ASYNC=0
export OPENERP_ADDONS_PATH="<ruta_erp>/server/bin/addons"
export OPENERP_DB_HOST="localhost"
export OPENERP_DB_NAME="<nom_bbdd_test>"
export OPENERP_DB_USER="erp"
export OPENERP_DB_PASSWORD="<password>"
export OPENERP_PRICE_ACCURACY=6
export OPENERP_SECRET="<secret>"
export OPENERP_ROOT_PATH="<ruta_erp>/server/bin/"
export OPENERP_REDIS_URL="redis://localhost"
export OPENERP_MONGODB_HOST="localhost"
export OPENERP_SII_TEST_MODE=1
export OPENERP_ENVIRONMENT=local
export OPENERP_RUN_SCRIPTS_INTERACTIVE_RESULT=skip
export DESTRAL_TESTING_LANGS="['es_ES']"
export PYTHONPATH="<ruta_erp>/server/bin:<ruta_erp>/server/bin/addons:<ruta_erp>/server/sitecustomize:$PYTHONPATH"
export PYTHONIOENCODING="UTF-8"
export PYTHONUNBUFFERED="1"
```

La CI s'executa via GitHub Actions (`.github/workflows/reusable_workflow.yml`).

---

## Estructura d'un mòdul

```
module_name/
├── __terp__.py          # Manifest del mòdul (name, version, depends, update_xml...)
├── __init__.py
├── models/              # Definicions de models (osv.osv)
├── views/               # Vistes XML
├── wizard/              # Wizards (osv.osv_memory)
├── workflow/            # Definicions de workflow XML
├── data/                # Dades estàtiques carregades en instal·lació
├── demo/                # Dades de demo
├── security/            # Control d'accés: ir.model.access.csv
├── migrations/          # Scripts de migració (oopgrade)
├── tests/               # Fitxers de test
│   ├── fixtures/        # Dades XML per als testos
│   └── tests_*.py
├── i18n/                # Traduccions
├── report/              # Informes
└── requirements.txt     # Dependències Python del mòdul
```

---

## Patrons d'arquitectura

### Definició de models

```python
from osv import osv, fields
from tools.translate import _

class MyModel(osv.osv):
    _name = "my.model.name"
    _columns = {
        "name": fields.char("Name", size=64),
        "related_id": fields.many2one("other.model", "Related"),
    }
MyModel()
```

Tots els mètodes reben `(cursor, uid, ids, ...)` com a primers arguments. Per accedir a altres models: `self.pool.get("model.name")`.

### Extensió de models GISCE/PowerERP

```python
class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"
    # Afegir columnes o sobreescriure mètodes
GiscedataPolissa()
```

### Jobs asíncrons

```python
from oorq.decorators import job

@job
def my_async_method(self, cursor, uid, ids, context=None):
    ...
```

### Excepcions

```python
raise osv.except_osv(_('Error !'), _('Missatge descriptiu'))
```

### Migracions

```python
from oopgrade.oopgrade import load_data

def up(cursor, installed_version):
    if not installed_version:
        return
    pool = pooler.get_pool(cursor.dbname)
    # SQL o model auto_init
```

### Patró de testos

```python
from destral import testing
from destral.transaction import Transaction

class TestsMyModule(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()
```

Referència a fixtures via `ir.model.data`:
```python
imd_o = self.openerp.pool.get("ir.model.data")
record_id = imd_o.get_object_reference(self.cursor, self.uid, "module_name", "xml_id")[1]
```

---

## Afegir un nou mòdul

1. Copiar la plantilla de `Som-Energia/erp_docs` (`som_template`).
2. Afegir un workflow a `.github/workflows/schedule_tests_<modul>.yml` (copiar un existent i canviar `name` i `module`).
3. Afegir el mòdul a `.github/labeler.yml`.
4. Afegir el mòdul a la taula del `README.md`.

---

## Dependències externes clau

L'entorn ERP depèn de diversos repositoris clonats al mateix nivell que aquest repo (`../`):

- `Som-Energia/erp` (PowerERP/OpenERP core, privat)
- `Som-Energia/libFacturacioATR`
- `Som-Energia/omie-modules` + `Som-Energia/OMIE`
- `Som-Energia/somenergia-generationkwh`
- `gisce/oorq` (cua de jobs asíncrons)
- `poweremail`, `openerp-sentry`, `ws_transactions`, `ir_attachment_mongodb`, `mongodb_backend`

---

## Convenció de commits

Els missatges de commit segueixen el format:

```
<emoji> (<modul o context>) Cosa que fa el commit
```

Emojis disponibles (basats en [gitmoji](https://gitmoji.dev/)):

| Emoji | Tipus |
|-------|-------|
| ✨ | Nova funcionalitat (feat) |
| 🐛 | Correcció de bug (fix) |
| 🩹 | Correcció menor (mini-fix) |
| 👔 | Lògica de negoci (business logic) |
| 🗃️ | Dades XML (data xml) |
| 🏗️ | Build / estructura |
| 🔧 | CI / configuració |
| 📝 | Documentació |
| ⚡️ | Rendiment (perf) |
| ♻️ | Refactorització |
| 🎨 | Estil de codi |
| 🧹 | Neteja (cleanup) |
| 🦺 | Codi robust |
| ✅ | Testos |
| 🚧 | Treball en curs (WIP) |
| 🌐 | Traduccions (i18n) |
| 💄 | Visual |
| 🏳️ | Abandonat (giveup) |
| 🐬 | Informes (reports) |
| 🔨 | Script de migració |

Exemples:
```
🐛 (som_polissa) Fix error en càlcul de factura
✨ (gurb) Afegir camp assigned_betas_kw al CAU
♻️ (switching) Refactoritzar _is_m1_closable
✅ (som_gurb) Afegir test per a totals de betes
```

---

## Desplegament

- **Producció (erp01)**: `git pull` a la branca `main`.
- **Testing (terp01)**: Treballa amb una branca Rolling; fusionar PRs amb `git merge origin/BRANCH_NAME`.
- **Servidors ad-hoc**: `sastre deploy --host ... --pr <PR_NUM> --owner Som-Energia --repository openerp_som_addons --environ test`.
