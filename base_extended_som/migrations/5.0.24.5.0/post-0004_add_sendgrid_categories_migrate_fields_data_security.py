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
    pool.get("poweremail.sendgrid.category")._auto_init(
        cursor, context={'module': 'base_extended_som'}
    )
    pool.get("poweremail.templates")._auto_init(
        cursor, context={'module': 'base_extended_som'}
    )

    logger.info("Updating XML files")
    data_files = [
        'views/poweremail_sendgrid_category_view.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'base_extended_som', data_file,
            idref=None, mode='update'
        )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'base_extended_som', security_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
