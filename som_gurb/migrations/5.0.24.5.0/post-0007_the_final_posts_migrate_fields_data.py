# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("som.gurb.cau")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )

    pool.get("som.gurb.group")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )

    logger.info("Updating XML files")
    data_files = [
        'views/som_gurb_cau_view.xml',
        'wizard/wizard_create_gurb_cups_signature_view.xml',
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
