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
    pool.get("wizard.reprint.invoice.som")._auto_init(
        cursor, context={'module': 'giscedata_facturacio_comer_som'}
    )

    logger.info("Updating XML files")
    data_files = [
        'security/giscedata_facturacio_comer_som.xml',
        'wizard/wizard_reprint_invoice_som.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'giscedata_facturacio_comer_som', data_file,
            idref=None, mode='update'
        )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'giscedata_facturacio_comer_som', security_file,
            idref=None, mode='update'
        )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
