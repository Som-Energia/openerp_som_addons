# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("res.partner")._auto_init(
        cursor, context={'module': 'som_partner_account'}
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
