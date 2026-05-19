# coding=utf-8

import logging

from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Creating models")
    pool.get("report.backend.mailcanvipreus.eie")._auto_init(
        cursor, context={'module': 'som_polissa_condicions_generals'}
    )

    logger.info("Table created succesfully.")

    # Actualitzar tots els permisos
    logger.info("Updating access CSV")
    load_data(
        cursor, 'som_polissa_condicions_generals', 'security/ir.model.access.csv',
        idref=None, mode='update'
    )
    logger.info("CSV succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
