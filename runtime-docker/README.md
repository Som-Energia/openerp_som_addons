# Datasets PostgreSQL com artefactes OCI

Sistema pragmàtic per distribuir snapshots PostgreSQL del runtime OpenERP/Odoo via ORAS i Harbor, sense tocar la imatge runtime.

## Camí feliç

Des de l'arrel del repo. Configura primer els fitxers d'entorn:

```bash
cp runtime-docker/.env.producer.example runtime-docker/.env.producer
cp runtime-docker/.env.consumer.example runtime-docker/.env.consumer
# edita valors (Harbor, repositori, tags, etc.)
```

1. Equip productor:

```bash
make -C runtime-docker dataset-producer-all
```

2. Equip consumidor:

```bash
make -C runtime-docker dataset-consumer-all
```

3. Opcional (mode local/dev amb override):

```bash
cp runtime-docker/docker-compose.consumer.override.example.yml runtime-docker/docker-compose.consumer.override.yml
# ajusta mounts si cal
make -C runtime-docker dataset-consumer-up-local
```

## Variables obligatòries (publicar a Harbor)

Per publicar (i per al smoke test dins VPN), aquestes variables són obligatòries:

- `HARBOR_DOMAIN`: domini del registry Harbor (ex: `harbor.example.com`)
- `HARBOR_USERNAME`: usuari amb permisos de push/pull al repositori
- `HARBOR_PASSWORD`: password o token de l'usuari

I aquesta és recomanada (si no la passes, es calcula sola):

- `HARBOR_DATASET_REPOSITORY`: repositori OCI complet (default: `${HARBOR_DOMAIN}/openerp/datasets`)

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
  - `dataset-consumer-sync`
  - `dataset-consumer-up`
  - `dataset-consumer-up-local`

També es mantenen aliases curts per compatibilitat:

- `dataset-create`
- `dataset-publish`
- `dataset-pull`
- `dataset-restore`

Això evita duplicar configuració i, alhora, deixa clar qui executa cada part del workflow.

Els targets `make` carreguen automàticament:

- `.env.producer` per targets productor i prewarmed.
- `.env.consumer` per targets consumidor.

## Arquitectura

- Origen de dades: servei `postgres` de `runtime-docker/docker-compose.yml`.
- Versions pinades de base de dades: PostgreSQL `13.14` + TimescaleDB `2.14.2` (imatge `timescale/timescaledb:2.14.2-pg13`).
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

El camí per defecte del productor (`runtime-docker/.env.producer`) és:

```bash
make -C runtime-docker dataset-producer-all
```

Això fa:

1. `runtime-build-prewarmed` (build + push de la imatge prewarmed)
2. `dataset-producer-publish` (push del dataset exportat)

Tags publicats per defecte (imatge i dataset):

- `latest`
- `YYYYMMDD` (data UTC)

Si abans has executat `runtime-build-prewarmed`, `dataset-producer-create` pot
reutilitzar automàticament el dump exportat del prewarm (`PREWARMED_DB_DUMP_PATH`)
i evitar tornar a executar destral.

Opció legacy (sense prewarm com a pas principal):

```bash
make -C runtime-docker dataset-producer-legacy-all
```

### Workflow consumidor

El consumidor només necessita (`runtime-docker/.env.consumer`):

```bash
make -C runtime-docker dataset-consumer-all
```

Això fa:
```bash
# 1) sincronitza imatge i dataset; restaura la base només si el dataset resolt és nou
make -C runtime-docker dataset-consumer-sync

# 2) arrenca el compose compartit (consumer pur)
make -C runtime-docker dataset-consumer-up

# 3) opcional: mateix stack i mateixa BD, però amb openerp_som_addons local
cp runtime-docker/docker-compose.consumer.override.example.yml runtime-docker/docker-compose.consumer.override.yml
make -C runtime-docker dataset-consumer-up-local
```

La sincronització guarda una marca local a `runtime-docker/.cache/consumer-state/dataset-state.env` amb:

- `requested_tag`: el tag demanat (`latest`, `YYYYMMDD`, ...)
- `resolved_tag`: el `dataset_version` real restaurat

Si falta aquesta marca, `dataset-consumer-sync` assumeix estat desconegut i restaura.

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
- crea sempre dos tags:
  - `latest`
  - data UTC (`YYYYMMDD`).

Variables útils:

- `HARBOR_DATASET_REPOSITORY`
- `DATASET_FILE`, `METADATA_FILE`
- `DATE_TAG`

### Descarregar dataset

`pull_dataset.sh`:

- baixa `HARBOR_DATASET_REPOSITORY:DATASET_TAG`,
- guarda el resultat a `runtime-docker/.cache/datasets/<tag>/`.

Variables útils:

- `HARBOR_DATASET_REPOSITORY`
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
set -a
source runtime-docker/.env.producer
set +a

printf '%s' "$HARBOR_PASSWORD" | docker login "$HARBOR_DOMAIN" -u "$HARBOR_USERNAME" --password-stdin
make -C runtime-docker dataset-producer-create
make -C runtime-docker dataset-producer-publish
```

## Smoke test complet (servidor dins VPN)

Executa el flux sencer (create -> publish -> pull -> restore):

```bash
# assegura que runtime-docker/.env.producer té credencials vàlides
make -C runtime-docker dataset-smoke-vpn
```

Opcionalment:

- `DATASET_TAG` (default: `latest`)
- `COMPOSE_FILE`, `DB_SERVICE`, `POSTGRES_DB`, `POSTGRES_USER`

## Restauració manual

Des de cache OCI:

```bash
# configura HARBOR_DATASET_REPOSITORY i DATASET_TAG a runtime-docker/.env.consumer
make -C runtime-docker dataset-consumer-pull
make -C runtime-docker dataset-consumer-restore
```

Des d'un fitxer concret:

```bash
# defineix DATASET_PATH a runtime-docker/.env.consumer
make -C runtime-docker dataset-consumer-restore
```

Contra un PostgreSQL extern:

```bash
# defineix POSTGRES_HOST, POSTGRES_PORT i POSTGRES_DB a runtime-docker/.env.consumer
make -C runtime-docker dataset-consumer-restore
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
- comparteix el mateix stack i la mateixa BD entre mode empaquetat i mode local,
- separa `dataset-consumer-sync` del `up`, per evitar refresh o restore accidental a cada arrencada.

Nota sobre `erp-runtime`:

- En mode consumidor per defecte **no** es munta `/opt/somenergia/src`, així s'executa exactament el codi de la imatge de Harbor.
- Si vols iterar codi local, fes servir `dataset-consumer-up-local` amb `docker-compose.consumer.override.yml`.
- El compose consumidor arrenca ERP directament amb `start-openerp-server.sh` (bypass de `build-openerp-server.sh`) per evitar executar `destral` a cada `up`.

### Opció recomanada: imatge prewarmed

Per evitar també el bootstrap del _primer_ arrencat, publica una imatge runtime
prewarmed. Aquest és el camí recomanat per equips consumidors: la imatge ja porta
repos clonats, dependències instal·lades i ERP preparat; el dataset es distribueix
separadament com a artefacte OCI.

Script inclòs:

- `runtime-docker/scripts/build_prewarmed_image.sh`
- targets Makefile:
  - `make -C runtime-docker runtime-build-prewarmed` (build + export DB + push imatge)
  - `make -C runtime-docker runtime-export-prewarmed-db` (només export DB prewarmed, sense push)

Variables obligatòries:

- `HARBOR_IMAGE_REPOSITORY` (ex: `harbor.example.com/erp/openerp`)
- `GITHUB_TOKEN` (read repos privats, només durant el build/prewarm)

Variables opcionals:

- `BASE_IMAGE`: si s'informa, el prewarm parteix d'una imatge existent.
- `LOCAL_BASE_IMAGE`: tag local per a la imatge base quan `BASE_IMAGE` no s'informa.
- `DOCKERFILE_PATH` i `BUILD_CONTEXT`: permeten canviar el Dockerfile/context del build base.

Exemple recomanat, construint també la base localment:

```bash
# defineix HARBOR_IMAGE_REPOSITORY i GITHUB_TOKEN a runtime-docker/.env.producer
make -C runtime-docker runtime-build-prewarmed

# si només vols regenerar el dump prewarmed local (sense publicar imatge):
make -C runtime-docker runtime-export-prewarmed-db
```

Exemple alternatiu, partint d'una base ja publicada:

```bash
# defineix BASE_IMAGE, HARBOR_IMAGE_REPOSITORY i GITHUB_TOKEN a runtime-docker/.env.producer
make -C runtime-docker runtime-build-prewarmed
```

El token de GitHub es passa al contenidor de bootstrap com a fitxer muntat temporal,
no com a variable d'entorn de Docker. Abans de fer el commit de la imatge final,
el script elimina les carpetes `.git` de la imatge perquè no cal historial ni
remotes en entorns consumidors.

A més, el prewarm exporta un dump de la BD temporal a
`PREWARMED_DB_DUMP_PATH` (per defecte `runtime-docker/build/prewarmed/prewarmed-db.dump.zst`).
Aquest dump es pot reaprofitar després a `dataset-producer-create` amb
`USE_PREWARMED_DB=1`.

Després, a l'equip consumidor:

```bash
ERP_RUNTIME_IMAGE="harbor.example.com/erp/openerp:latest"
```

### Arrencar stack de consum

Modes disponibles:

- `dataset-consumer-up`: consumer pur (imatge Harbor, sense mounts locals), sense fer cap sync ni restore.
- `dataset-consumer-up-local`: usa `docker-compose.consumer.override.yml` per mounts locals sobre el mateix stack i la mateixa BD.
- `dataset-consumer-sync`: actualitza la imatge si canvia i restaura la BD només quan el dataset resolt és nou.
- `dataset-consumer-refresh`: recrea el stack consumer pur sense tocar l'estat sincronitzat.


```bash
cp runtime-docker/.env.consumer.example runtime-docker/.env.consumer
# edita credencials Harbor i valors necessaris

make -C runtime-docker dataset-consumer-sync
make -C runtime-docker dataset-consumer-up
```

### Forçar una restauració del dataset actual

```bash
FORCE_RESTORE=1 make -C runtime-docker dataset-consumer-sync
```

### Carregar manualment el dataset actual a PostgreSQL local

```bash
make -C runtime-docker dataset-consumer-restore
```

Variables obligatòries per aquest flux:

- `HARBOR_DOMAIN`
- `HARBOR_USERNAME`
- `HARBOR_PASSWORD`

Variables recomanades:

- `ERP_RUNTIME_IMAGE` (default: `harbor.example.com/erp/openerp:latest`)
- `GITHUB_TOKEN` (opcional en mode consumidor amb entrypoint bypass)
- `HARBOR_DATASET_REPOSITORY` (default: `harbor.example.com/erp/datasets`)
- `DATASET_TAG` (default: `latest`)
- `RESET_ADMIN_LOGIN` (default: `admin`)
- `RESET_ADMIN_PASSWORD` (recomanat: `admin` en entorns locals de demo)

Troubleshooting ràpid:

- Si el contenidor carrega codi antic tot i fer pull, comprova que no estiguis en mode local (`dataset-consumer-up-local`) amb mounts que tapen `/opt/somenergia/src`.

- Si `dataset-consumer-sync` no restaura quan esperaves, revisa `runtime-docker/.cache/consumer-state/dataset-state.env` per veure quin `resolved_tag` considera aplicat.

- Si veus `artifact erp/openerp:latest not found`, revisa que `ERP_RUNTIME_IMAGE` sigui una referència completa i existent a Harbor.
- Pots validar la interpolació final amb:

```bash
docker compose --env-file runtime-docker/.env.consumer -f runtime-docker/docker-compose.consumer.yml config | grep -A2 'erp-runtime:'
```
