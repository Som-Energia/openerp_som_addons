# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Update models giscedata.polissa and giscedata.polissa.modcontractual")
    pool.get('giscedata.polissa')._auto_init(
        cursor, context={'module': 'som_auvidi'}
    )
    pool.get('giscedata.polissa.modcontractual')._auto_init(
        cursor, context={'module': 'som_auvidi'}
    )
    logger.info("Models updated")


def down(cursor, installed_version):
    pass


migrate = up
