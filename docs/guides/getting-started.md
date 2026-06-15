# Getting Started

## Configuració de l'entorn

### Requisits

- Python 2.7 (compatible amb Python 3)
- Virtualenv accessible des de `pyenv activate erp` o `workon erp`
- Docker (PostgreSQL, MongoDB, Redis)
- Docker Compose: `docker-compose.yaml` al arrel del repositori

### Arrancar bases de dades
- OpenERP instal·lat a `~/somenergia/src/erp/server/bin`

### Variables d'entorn

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

## Arrancar un ERP

Consulta el skill [erp-start](../../.agents/skills/erp-start/SKILL.md) per arrencar el servei, verificar contenidors i executar l'ERP localment.

## Executar tests

Consulta el skill [erp-test](../../.agents/skills/erp-test/SKILL.md) per executar tests automatitzats amb destral.

## Scripts de migració

Consulta el skill [erp-migration](../../.agents/skills/erp-migration/SKILL.md) per crear scripts de migració quan es modifiquen models o fitxers XML.

## Afegir un nou mòdul

1. Copiar la plantilla de `Som-Energia/erp_docs` (`som_template`)
2. Afegir un workflow a `.github/workflows/schedule_tests_<modul>.yml`
3. Afegir el mòdul a `.github/labeler.yml`
4. Afegir el mòdul a la taula del `README.md`

## Dependències externes

L'entorn ERP depén de diversos repositoris clonats al mateix nivell que aquest repo (`../`):

- `Som-Energia/erp` (PowerERP/OpenERP core, privat)
- `Som-Energia/libFacturacioATR`
- `Som-Energia/omie-modules` + `Som-Energia/OMIE`
- `Som-Energia/somenergia-generationkwh`
- `gisce/oorq` (cua de jobs asíncrons)
- `poweremail`, `openerp-sentry`, `ws_transactions`, `ir_attachment_mongodb`, `mongodb_backend`

## Desplegament

- **Producció (erp01)**: `git pull` a la branca `main`
- **Testing (terp01)**: Treballa amb una branca Rolling; fusionar PRs amb `git merge origin/BRANCH_NAME`
- **Servidors ad-hoc**: `sastre deploy --host ... --pr <PR_NUM> --owner Som-Energia --repository openerp_som_addons --environ test`

## Per saber-ne més

- **Receptes pràctiques**: [docs/patterns/](../patterns/)
- **Arquitectura**: [.github/docs/arquitectura.md](../../.github/docs/arquitectura.md)
- **Convencions de commit**: [.github/docs/desenvolupament.md](../../.github/docs/desenvolupament.md)
