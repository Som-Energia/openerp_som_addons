# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records, load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating soci and category CT campaign")
    data_records = ["origen_ct_sense_socia"]
    load_data_records(
        cursor, 'som_polissa_soci', 'giscedata_polissa_category_data.xml', data_records,
        mode='update'
    )
    load_data(
        cursor, 'som_polissa_soci', 'somenergia_soci_data.xml',
        mode='init'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
