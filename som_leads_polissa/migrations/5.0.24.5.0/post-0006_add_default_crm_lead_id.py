# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Initializing new fields")
    pool.get("giscedata.crm.lead")._auto_init(
        cursor, context={'module': 'som_leads_polissa'}
    )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
