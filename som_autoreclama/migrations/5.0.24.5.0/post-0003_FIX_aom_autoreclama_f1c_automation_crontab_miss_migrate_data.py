# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    data_files = [
        'som_autoreclama_state_data.xml',
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
