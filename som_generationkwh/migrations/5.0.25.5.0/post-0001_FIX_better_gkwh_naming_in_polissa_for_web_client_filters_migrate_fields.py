# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Reinitializing field metadata for renamed te_assignacio_gkwh label")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("giscedata.polissa")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
