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
    pool.get("giscedata.facturacio.factura")._auto_init(
        cursor, context={'module': 'som_card_payment'}
    )

    logger.info("Updating XML files")
    data_files = [
        'data/email_template_data.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_card_payment', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
