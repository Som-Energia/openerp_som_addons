# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data
from tools import config


def up(cursor, installed_version):
    if not installed_version:
        return
    if config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Creating new wizard wizard.generate.cau.migration.file")
    pool.get("wizard.generate.cau.migration.file")._auto_init(
        cursor, context={'module': 'som_polissa'}
    )
    logger.info("Fields created successfully")

    logger.info("Updating XML wizard_generate_cau_migration_file_view.xml")
    load_data(
        cursor, 'som_polissa', 'wizard/wizard_generate_cau_migration_file_view.xml', idref=None,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
