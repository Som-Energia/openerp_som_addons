# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler


def up(cursor, installed_version):
    logger = logging.getLogger('openerp.migration')

    if not installed_version:
        return

    pool = pooler.get_pool(cursor.dbname)
    uid = 1
    pricelist_obj = pool.get('product.pricelist')
    if not pricelist_obj or not hasattr(pricelist_obj, 'migrate_indexed_formulas'):
        logger.warning('Skipping indexed formula migration: migrate_indexed_formulas not available')
        return

    pricelist_obj.migrate_indexed_formulas(cursor, uid, {})


def down(cursor, installed_version):
    pass


migrate = up
