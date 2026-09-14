# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Initializing som.card.payment.helper metadata in www_som")
    pool.get("som.card.payment.helper")._auto_init(
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
