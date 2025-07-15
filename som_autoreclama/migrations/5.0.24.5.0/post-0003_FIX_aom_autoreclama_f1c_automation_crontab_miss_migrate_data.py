# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML files")
    data_files = [

    ]
    for data_file in data_files:
        load_data_records(
            cursor,
            'som_autoreclama',
            'som_autoreclama_state_data.xml',
            ["ir_cron_autoreclama_f1c_automation"],
            mode='update'
        )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
