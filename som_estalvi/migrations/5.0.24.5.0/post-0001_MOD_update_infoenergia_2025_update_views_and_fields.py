# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pooler.get_pool(cursor.dbname)

    logger.info("Updating XML and CSV files")
    data_files = [
        'wizard/wizard_contract_power_optimization_view.xml',
    ]

    for data_file in data_files:
        load_data(
            cursor, 'som_estalvi', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
