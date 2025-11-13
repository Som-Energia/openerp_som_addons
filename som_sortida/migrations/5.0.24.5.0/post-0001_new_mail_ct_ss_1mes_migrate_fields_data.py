# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data, delete_record
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("giscedata.polissa")._auto_init(
        cursor, context={'module': 'som_sortida'}
    )

    logger.info('Deleting old config')
    delete_record(cursor, 'som_sortida', ['config_llista_nifs_socia_promocional'])

    logger.info("Updating XML files")
    data_files = [
        'data/som_sortida_data.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_sortida', data_file,
            idref=None, mode='update'
        )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
