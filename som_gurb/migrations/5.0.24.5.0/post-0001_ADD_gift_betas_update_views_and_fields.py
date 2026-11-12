# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Initializing new fields")
    pool.get("som.gurb")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )
    pool.get("som.gurb.general.conditions")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )
    pool.get("som.gurb.cups")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )
    pool.get("som.gurb.cups.beta")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )

    logger.info("Updating XML and CSV files")
    data_files = [
        'data/som_gurb_data.xml',
        'views/som_gurb_cups_view.xml',
        'views/som_gurb_view.xml',
        'wizard/wizard_gurb_create_new_beta_view.xml',
    ]

    for data_file in data_files:
        load_data(
            cursor, 'som_gurb', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
