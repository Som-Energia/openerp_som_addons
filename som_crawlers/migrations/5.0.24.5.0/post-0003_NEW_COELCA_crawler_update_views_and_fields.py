# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML files")
    data_files = [
        'data/som_crawlers_config_data.xml',
        'data/som_crawlers_task_data.xml',
        'data/som_crawlers_step_data.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_crawlers', data_file,
            idref=None, mode='update'
        )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
