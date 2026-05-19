# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML and CSV files")
    data_files = [
        'som_dashboard_gc_fase_3.xml',
        'som_dashboard_gc_tasca_1.xml',
        'som_dashboard_gc_endarrerits.xml',
    ]

    for data_file in data_files:
        load_data(
            cursor, 'som_dashboard', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
