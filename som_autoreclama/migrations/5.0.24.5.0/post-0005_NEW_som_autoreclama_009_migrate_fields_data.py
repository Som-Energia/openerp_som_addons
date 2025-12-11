# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    logger.info("Updating XML files")
    data_files = [
        'data/giscedata_atc_tag_data.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_autoreclama', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
