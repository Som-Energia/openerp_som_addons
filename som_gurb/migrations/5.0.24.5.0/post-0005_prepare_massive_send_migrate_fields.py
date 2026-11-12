# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("som.gurb.group")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
