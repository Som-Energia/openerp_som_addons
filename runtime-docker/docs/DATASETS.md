# Datasets PostgreSQL com artefactes OCI

Sistema pragmàtic per distribuir snapshots PostgreSQL del runtime OpenERP/Odoo via ORAS i Harbor, sense tocar la imatge runtime.

## Camí feliç

Des de l'arrel del repo:

1. Equip productor: crear dataset:

```bash
make -C runtime-docker dataset-producer-create
```

2. Equip productor: publicar-lo a Harbor:

```bash
DATASET_REPOSITORY="harbor.example.com/openerp/datasets" make -C runtime-docker dataset-producer-publish
```

3. Equip consumidor: descarregar l'últim dataset:

```bash
make -C runtime-docker dataset-consumer-pull
```

4. Equip consumidor: restaurar-lo al PostgreSQL del runtime local:

```bash
make -C runtime-docker dataset-consumer-restore
```

## Variables obligatòries (publicar a Harbor)

Per publicar (i per al smoke test dins VPN), aquestes variables són obligatòries:

- `HARBOR_DOMAIN`: domini del registry Harbor (ex: `harbor.example.com`)
- `HARBOR_USERNAME`: usuari amb permisos de push/pull al repositori
- `HARBOR_PASSWORD`: password o token de l'usuari

I aquesta és recomanada (si no la passes, es calcula sola):

- `DATASET_REPOSITORY`: repositori OCI complet (default: `${HARBOR_DOMAIN}/openerp/datasets`)

Variables habituals de runtime:

- `COMPOSE_FILE` (default: `runtime-docker/docker-compose.yml`)
- `DB_SERVICE` (default: `postgres`)
- `POSTGRES_DB` o `ERP_DATABASE` (default: `erp_runtime`)
- `POSTGRES_USER` (default: `erp`)
- `EXPECTED_POSTGRES_MAJOR` (default: `13`, recomanat deixar-lo així per alinear amb PROD)

Política de versió:
- Els scripts validen la versió del servidor PostgreSQL abans de crear/restaurar.
- Si no és major `13`, fallen amb error explícit.

## Rols i entrypoints

Fem servir un sol `Makefile`, però separat per rols:

- Productor:
  - `dataset-producer-create`
  - `dataset-producer-publish`
- Consumidor:
  - `dataset-consumer-pull`
  - `dataset-consumer-restore`

També es mantenen aliases curts per compatibilitat:

- `dataset-create`
- `dataset-publish`
- `dataset-pull`
- `dataset-restore`

Això evita duplicar configuració i, alhora, deixa clar qui executa cada part del workflow.

## Arquitectura

- Origen de dades: servei `postgres` de `runtime-docker/docker-compose.yml`.
- Format de dump: `pg_dump -Fc`.
- Compressió: `zstd`.
- Distribució: OCI artifacts via `oras push` i `oras pull`.
- Registry: Harbor o qualsevol registry OCI compatible.
- Cache local: `runtime-docker/.cache/datasets/<tag>/`.

## Estructura

- `runtime-docker/scripts/create_dataset.sh` — crea dump, compressió i metadata.
- `runtime-docker/scripts/publish_dataset.sh` — publica dump i metadata a Harbor.
- `runtime-docker/scripts/pull_dataset.sh` — descarrega un dataset a cache local.
- `runtime-docker/scripts/restore_dataset.sh` — restaura el dataset en local.
- `runtime-docker/datasets/metadata.json` — plantilla de metadata.
- `runtime-docker/docker-compose.override.example.yml` — override opcional per exposar PostgreSQL.

## Workflow

### Workflow productor

El productor només necessita:

```bash
make -C runtime-docker dataset-producer-create
DATASET_REPOSITORY="harbor.example.com/openerp/datasets" make -C runtime-docker dataset-producer-publish
```

### Workflow consumidor

El consumidor només necessita:

```bash
DATASET_REPOSITORY="harbor.example.com/openerp/datasets" DATASET_TAG=latest make -C runtime-docker dataset-consumer-pull
make -C runtime-docker dataset-consumer-restore
```

### Crear dataset

`create_dataset.sh`:
- arrenca `postgres` si cal,
- espera `pg_isready`,
- executa `pg_dump -Fc`,
- comprimeix amb `zstd`,
- calcula `sha256`,
- escriu metadata JSON a `runtime-docker/build/datasets/`.

Sortida:
- `runtime-docker/build/datasets/openerp-demo-YYYYMMDD.dump.zst`
- `runtime-docker/build/datasets/openerp-demo-YYYYMMDD.metadata.json`

Variables útils:
- `DATASET_NAME`
- `POSTGRES_DB` o `ERP_DATABASE`
- `POSTGRES_USER`
- `COMPOSE_FILE`, `DB_SERVICE`
- `ODOO_VERSION`
- `EXCLUDE_TIMESCALE_INTERNALS` (default: `1`)
- `PG_DUMP_EXTRA_ARGS` (opcions addicionals de `pg_dump`)

Nota TimescaleDB:
- Per defecte, el dump exclou esquemes interns `_timescaledb_*` per evitar errors de restore entre entorns.
- Si necessites incloure'ls explícitament, posa `EXCLUDE_TIMESCALE_INTERNALS=0`.

### Publicar a Harbor

`publish_dataset.sh`:
- reutilitza el login existent del Docker client,
- publica dump i metadata via `oras push`,
- crea sempre tres tags:
  - `latest`
  - timestamp UTC (`YYYYMMDDHHMMSS`)
  - git sha curt.

Variables útils:
- `DATASET_REPOSITORY`
- `DATASET_FILE`, `METADATA_FILE`
- `TIMESTAMP_TAG`, `GIT_SHA_TAG`

### Descarregar dataset

`pull_dataset.sh`:
- baixa `DATASET_REPOSITORY:DATASET_TAG`,
- guarda el resultat a `runtime-docker/.cache/datasets/<tag>/`.

Variables útils:
- `DATASET_REPOSITORY`
- `DATASET_TAG`
- `CACHE_DIR`

### Restaurar dataset

`restore_dataset.sh` té dos modes:

- Mode compose per defecte: si `POSTGRES_HOST` no està definit, restaura directament dins del contenidor `postgres`.
- Mode extern: si defines `POSTGRES_HOST`, fa servir `dropdb`, `createdb` i `pg_restore` contra aquell host.

Variables útils:
- `POSTGRES_HOST`, `POSTGRES_PORT`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `POSTGRES_DB` o `ERP_DATABASE`
- `DATASET_PATH` o `DATASET_TAG`
- `COMPOSE_FILE`, `DB_SERVICE`
- `RESET_ADMIN_LOGIN` (default: `admin`)
- `RESET_ADMIN_PASSWORD` (si s'informa, es força després del restore)

## Publicació manual

```bash
export HARBOR_DOMAIN="harbor.example.com"
export HARBOR_USERNAME="<usuari>"
export HARBOR_PASSWORD="<password_o_token>"
export DATASET_REPOSITORY="${HARBOR_DOMAIN}/openerp/datasets"

printf '%s' "$HARBOR_PASSWORD" | docker login "$HARBOR_DOMAIN" -u "$HARBOR_USERNAME" --password-stdin
make -C runtime-docker dataset-producer-create
make -C runtime-docker dataset-producer-publish
```

## Smoke test complet (servidor dins VPN)

Executa el flux sencer (create -> publish -> pull -> restore):

```bash
export HARBOR_DOMAIN="harbor.example.com"
export HARBOR_USERNAME="<usuari>"
export HARBOR_PASSWORD="<password_o_token>"
export DATASET_REPOSITORY="${HARBOR_DOMAIN}/openerp/datasets"

make -C runtime-docker dataset-smoke-vpn
```

Opcionalment:

- `DATASET_TAG` (default: `latest`)
- `COMPOSE_FILE`, `DB_SERVICE`, `POSTGRES_DB`, `POSTGRES_USER`

## Restauració manual

Des de cache OCI:

```bash
DATASET_REPOSITORY="harbor.example.com/openerp/datasets" DATASET_TAG=latest make -C runtime-docker dataset-consumer-pull
make -C runtime-docker dataset-consumer-restore
```

Des d'un fitxer concret:

```bash
DATASET_PATH="$PWD/runtime-docker/build/datasets/openerp-demo-20260515.dump.zst" make -C runtime-docker dataset-consumer-restore
```

Contra un PostgreSQL extern:

```bash
POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5432 POSTGRES_DB=erp_runtime make -C runtime-docker dataset-consumer-restore
```

## Integració operativa

Com que Harbor és local i darrere VPN, la publicació s'ha de fer des d'un host intern amb accés a la VPN.

Recomanació:
- executar `make -C runtime-docker dataset-smoke-vpn` com a comprovació inicial,
- després deixar un cron o job intern que executi només productor (`dataset-producer-create` + `dataset-producer-publish`).

## Docker Compose per equip consumidor

S'inclou un compose dedicat per consumidors:

- `runtime-docker/docker-compose.consumer.yml`
- `runtime-docker/.env.consumer.example`

Què fa:
- aixeca `postgres` (PG13), `mongo`, `redis` i `erp-runtime` (imatge preconstruida),
- permet executar un job one-shot `dataset-restore` que baixa `erp/datasets:latest` via ORAS i restaura la base.

Nota sobre `erp-runtime`:
- Aquesta imatge executa un bootstrap al primer inici (clonat/configuració) si no troba workspace.
- El compose consumidor munta un volum (`consumer_workspace`) a `/opt/somenergia/src` per persistir-lo i evitar re-bootstrap a cada arrencada.
- El compose consumidor arrenca ERP directament amb `start-openerp-server.sh` (bypass de `build-openerp-server.sh`) per evitar executar `destral` a cada `up`.

### Opció recomanada: imatge prewarmed

Per evitar també el bootstrap del *primer* arrencat, publica una imatge runtime prewarmed.

Script inclòs:
- `runtime-docker/scripts/build_prewarmed_image.sh`
- target Makefile: `make -C runtime-docker runtime-build-prewarmed`

Variables obligatòries:
- `BASE_IMAGE` (ex: `harbor.example.com/erp/openerp:20260514`)
- `TARGET_IMAGE` (ex: `harbor.example.com/erp/openerp:20260514-prewarmed`)
- `GITHUB_TOKEN` (read repos privats)

Exemple:

```bash
BASE_IMAGE="harbor.example.com/erp/openerp:20260514" \
TARGET_IMAGE="harbor.example.com/erp/openerp:20260514-prewarmed" \
GITHUB_TOKEN="<token>" \
make -C runtime-docker runtime-build-prewarmed
```

Després, a l'equip consumidor:

```bash
ERP_RUNTIME_IMAGE="harbor.example.com/erp/openerp:20260514-prewarmed"
```

### Arrencar stack de consum

```bash
cp runtime-docker/.env.consumer.example runtime-docker/.env.consumer
# edita credencials Harbor i valors necessaris

docker compose --env-file runtime-docker/.env.consumer -f runtime-docker/docker-compose.consumer.yml up -d postgres mongo redis erp-runtime
```

### Carregar el dataset més recent

```bash
docker compose --env-file runtime-docker/.env.consumer -f runtime-docker/docker-compose.consumer.yml --profile dataset run --rm dataset-restore
```

Variables obligatòries per aquest flux:
- `HARBOR_DOMAIN`
- `HARBOR_USERNAME`
- `HARBOR_PASSWORD`

Variables recomanades:
- `ERP_RUNTIME_IMAGE` (default: `harbor.example.com/erp/openerp:latest`)
- `GITHUB_TOKEN` (opcional en mode consumidor amb entrypoint bypass)
- `DATASET_REPOSITORY` (default: `harbor.example.com/erp/datasets`)
- `DATASET_TAG` (default: `latest`)
- `RESET_ADMIN_LOGIN` (default: `admin`)
- `RESET_ADMIN_PASSWORD` (recomanat: `admin` en entorns locals de demo)

Troubleshooting ràpid:
- Si veus `artifact erp/openerp:latest not found`, revisa que `ERP_RUNTIME_IMAGE` sigui una referència completa i existent a Harbor.
- Pots validar la interpolació final amb:

```bash
docker compose --env-file runtime-docker/.env.consumer -f runtime-docker/docker-compose.consumer.yml config | grep -A2 'erp-runtime:'
```
