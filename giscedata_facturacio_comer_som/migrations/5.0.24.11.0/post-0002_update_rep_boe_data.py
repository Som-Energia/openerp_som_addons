# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XMLs")

    list_of_records = [
        "rep_boe_data",
    ]
    load_data_records(
        cursor,
        'giscedata_facturacio_comer_som',
        'giscedata_facturacio_comer_data.xml',
        list_of_records,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
