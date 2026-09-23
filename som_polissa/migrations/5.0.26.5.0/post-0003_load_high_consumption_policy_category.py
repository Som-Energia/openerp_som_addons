# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Loading high consumption policy category")
    load_data_records(
        cursor, 'som_polissa', 'som_polissa_data.xml',
        ['categ_high_consumption_policy'], mode='update'
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
