# -*- coding: utf-8 -*-
import logging
from tools import config
from oopgrade.oopgrade import add_columns_fk, column_exists, load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Create enviat_mail_id column  in giscedata_facturacio_factura")
    if not column_exists(cursor, 'giscedata_facturacio_factura', 'enviat_mail_id'):
        new_column_spec = [('enviat_mail_id', 'int', 'poweremail_mailbox', 'id', 'set null')]
        add_columns_fk(cursor, {'giscedata_facturacio_factura': new_column_spec})
        logger.info("Column created succesfully.")
    else:
        logger.info("Column already created!!.")

    logger.info("Updating giscedata_facturacio_factura.xml")
    load_data(
        cursor,
        'giscedata_facturacio_comer_som',
        'giscedata_facturacio_factura.xml',
        idref=None,
        mode='update'
    )
    load_data_records(
        cursor,
        'giscedata_facturacio_comer_som',
        'giscedata_facturacio_comer_data.xml',
        ["fatura_pdf_cache_flags"],
        mode='update'
    )
    logger.info("XMLs succesfully updated.")

    # Run the script: manual_migration.py


def down(cursor, installed_version):
    pass


migrate = up
