# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating Task 1 M attachment dashboard filters")
    load_data_records(
        cursor,
        'som_dashboard',
        'som_dashboard_gc_tasca_1.xml',
        [
            'action_ms_with_attachments_dashboard',
            'action_ms_without_attachments_dashboard',
        ],
        mode='update'
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
