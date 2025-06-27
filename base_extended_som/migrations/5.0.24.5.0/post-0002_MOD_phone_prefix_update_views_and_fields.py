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
    pool.get("res.partner.address")._auto_init(
        cursor, context={'module': 'base_extended_som'}
    )

    pool.get("res.phone.national.code")._auto_init(
        cursor, context={'module': 'base_extended_som'}
    )

    logger.info("Updating XML files")
    data_files = [
        'data/base_extended_som_data.xml',
        'data/res_phone_national_code_data.xml',
        'views/res_partner_view.xml',
        'views/res_partner_address_view.xml',
        'views/res_phone_national_code_view.xml',
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
