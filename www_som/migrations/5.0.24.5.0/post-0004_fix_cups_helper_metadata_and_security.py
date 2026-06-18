# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Moving cups.helper metadata to www_som")
    cursor.execute('''
        UPDATE ir_model_data
        SET module = 'www_som'
        WHERE module = 'som_gurb'
        AND model = 'ir.model'
        AND name = 'model_cups_helper'
    ''')

    logger.info("Initializing cups.helper metadata in www_som")
    pool.get("cups.helper")._auto_init(
        cursor, context={'module': 'www_som'}
    )

    logger.info("Updating access rules")
    load_data(
        cursor, 'www_som', 'security/ir.model.access.csv',
        idref=None, mode='update'
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
