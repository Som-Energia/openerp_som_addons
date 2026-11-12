# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Initializing refund/rectify line validation metadata")
    pool = pooler.get_pool(cursor.dbname)
    pool.get("refund.rectify.batch.line")._auto_init(
        cursor, context={"module": "som_facturacio_switching"}
    )
    # No business backfill: old lines were not evaluated by this feature.
    # Do not overwrite snapshots if this script is run again.
    cursor.execute(
        "UPDATE refund_rectify_batch_line SET validation_evaluated=FALSE "
        "WHERE validation_evaluated IS NULL"
    )
    cursor.execute(
        "UPDATE refund_rectify_batch_line SET validation_warning_count=0 "
        "WHERE validation_warning_count IS NULL"
    )
    cursor.execute(
        "UPDATE refund_rectify_batch_line SET validation_warnings='' "
        "WHERE validation_warnings IS NULL"
    )
    load_data(
        cursor, 'som_facturacio_switching', 'refund_rectify_batch_view.xml',
        idref=None, mode='update'
    )
    logger.info("Refund/rectify validation metadata migration completed")


def down(cursor, installed_version):
    pass


migrate = up
