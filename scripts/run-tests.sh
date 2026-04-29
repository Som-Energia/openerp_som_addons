#!/bin/bash

# WORKSPACE: carpeta arrel on hi ha tots els repositoris del projecte
# Ex: export WORKSPACE=/home/<user>/src o /home/<user>/projects
: "${WORKSPACE:?WORKSPACE no definit. Ex: export WORKSPACE=/home/<user>/src}"

export PYTHONIOENCODING="UTF-8"
export PYTHONPATH="$WORKSPACE/erp/server/bin:$WORKSPACE/erp/server/bin/addons:$WORKSPACE/erp/server/sitecustomize:$PYTHONPATH"
export PYTHONUNBUFFERED="1"

export DEBUG_ENABLED=0
export OORQ_ASYNC=0
export DESTRAL_TESTING_LANGS="['es_ES']"

# export OPENERP_DB_NAME="destral_db"

export OPENERP_ADDONS_PATH="$WORKSPACE/erp/server/bin/addons"
export OPENERP_DB_HOST="localhost"
export OPENERP_DB_USER="erp"
export OPENERP_DB_PASSWORD="123456789"
export OPENERP_OORQ_ASYNC="False"
export OPENERP_PRICE_ACCURACY=6
export OPENERP_SECRET="1234567890"
export OPENERP_ROOT_PATH="$WORKSPACE/erp/server/bin/"
export OPENERP_REDIS_URL="redis://localhost"
export OPENERP_MONGODB_HOST="localhost"
export OPENERP_RUN_SCRIPTS_INTERACTIVE_RESULT=skip
export OPENERP_ENVIRONMENT=local
export OPENERP_SII_TEST_MODE=1

# --no-requirements evita que destral intenti instal·lar dependències (recomanat en entorns locals)
python $WORKSPACE/destral/destral/cli.py "$@"
