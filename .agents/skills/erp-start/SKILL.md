---
name: erp-start
description: >
  Arrenca el servei OpenERP/Som Energia localment.
  Automatitza: verificar contenidors, carregar variables d'entorn, executar openerp-server.
  Trigger: Quan necessites arrencar el servei ERP, executar l'ERP, o obrir l'entorn de desenvolupament.
metadata:
  author: oriol
  version: "1.0"
---

## When to Use

Utilitza aquesta skill quan:
- Necessites arrencar el servei ERP per testejar manualment
- Vols obrir l'interfície web d'OpenERP
- Estàs desenvolupant i necessites el servidor corrent

## Configuració Requerida

Aquesta skill requereix:
1. **Virtualenv activat** amb openerp-server instal·lat. El nom habitual és `erp`:
   - pyenv: `pyenv activate erp`
   - virtualenvwrapper: `workon erp`
2. **Contenidors Docker**: PostgreSQL, MongoDB, Redis

## Workflow

### Pas 1: Verificar Contenidors

```bash
docker ps --format "{{.Names}}" | grep -E "postgres|redis|mongo"
```

Contenidors esperats:
- PostgreSQL (src_db_1)
- MongoDB (src_mongo_1)
- Redis (src_redis_1)

Si no estan actius:
```bash
docker-compose up -d
```

### Pas 2: Arrencar l'ERP

**Amb alias** (recomanat):
```bash
erpserver -d <nom_bbdd>
```

**Amb comanda completa**:
```bash
/home/oriol/somenergia/src/erp/server/bin/openerp-server.py \
  --no-netrpc \
  --price_accuracy=6 \
  --config=$HOME/conf/erp.conf \
  -d <nom_bbdd>
```

**Opcions útils**:
```bash
# Actualitzar un mòdul en arrencar
erpserver -d <nom_bbdd> --update=<nom_modul>

# Executar només scripts de migració
erpserver -d <nom_bbdd> --run-scripts=<nom_modul>
```

### Pas 3: Accedir a la interfície

Un cop arrencat, l'ERP està disponible a:
- URL: `http://localhost:8069`
- Usuari: `admin`
- Contrasenya: La definida a la configuració

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| `openerp-server.py: command not found` | Virtualenv no activat | `pyenv activate erp` o `workon erp` |
| `Connection refused to localhost:5432` | PostgreSQL no corrent | `docker-compose up -d` |
| `Connection refused to localhost:27017` | MongoDB no corrent | `docker-compose up -d` |
| `Connection refused to localhost:6379` | Redis no corrent | `docker-compose up -d` |
| `Config file not found` | Fitxer de configuració inexistent | Crear `$HOME/conf/erp.conf` |

## Variables d'Entorn

Si executes manualment, cal carregar:
```bash
export OORQ_ASYNC=0
export OPENERP_ADDONS_PATH="<ruta_erp>/server/bin/addons"
export OPENERP_DB_HOST="localhost"
export OPENERP_DB_NAME="<nom_bbdd>"
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
