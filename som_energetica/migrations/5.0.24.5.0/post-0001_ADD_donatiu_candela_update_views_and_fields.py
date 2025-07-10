# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML files")
    data_files = [
        'data/giscedata_facturacio_data.xml',
        'data/som_energetica_data.xml',
        'views/som_energetica_view.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_energetica', data_file,
            idref=None, mode='update'
        )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
