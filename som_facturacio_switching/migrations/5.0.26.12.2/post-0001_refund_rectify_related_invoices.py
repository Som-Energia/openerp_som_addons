# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Initializing refund/rectify line source invoice relation schema")
    pool = pooler.get_pool(cursor.dbname)
    # Creates the source M2M relation; the nonstored supplier field needs no table.
    # Do not backfill historical sources or recompute validation/business data.
    pool.get("refund.rectify.batch.line")._auto_init(
        cursor, context={"module": "som_facturacio_switching"}
    )
    logger.info("Updating refund/rectify batch views with related invoice groups")
    load_data(
        cursor, 'som_facturacio_switching', 'refund_rectify_batch_view.xml',
        idref=None, mode='update'
    )
    logger.info("Refund/rectify related invoice schema/view migration completed")


def down(cursor, installed_version):
    pass


migrate = up
