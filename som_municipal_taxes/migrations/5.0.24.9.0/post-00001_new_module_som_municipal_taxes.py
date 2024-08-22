# -*- encoding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    #  Actualitzar un no mòdul al crear-lo i afegir una columna
    logger.info("Creating table: som.municipal.taxes.config")
    pool.get("som.municipal.taxes.config")._auto_init(
        cursor, context={'module': 'som_municipal_taxes'}
    )
    logger.info("Table created succesfully.")
    logger.info("Creating table: som.municipal.taxes.payment")
    pool.get("som.municipal.taxes.config")._auto_init(
        cursor, context={'module': 'som_municipal_taxes'}
    )
    logger.info("Table created succesfully.")


def down(cursor, installed_version):
    pass


migrate = up
