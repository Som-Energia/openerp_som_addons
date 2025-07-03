# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    wiz_obj = pool.get('wizard.calculate.gurb.savings')
    wiz_obj._auto_init(cursor, context={'module': 'som_gurb'})

    logger.info("Updating XML and CSV files")
    data_files = [
        'security/ir.model.access.csv',
        'wizard/wizard_calculate_gurb_savings_view.xml',
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
