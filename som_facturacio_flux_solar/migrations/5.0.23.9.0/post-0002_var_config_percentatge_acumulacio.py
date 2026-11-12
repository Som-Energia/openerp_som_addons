# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML records")
    data_file = 'giscedata_bateria_virtual_percentatges_acumulacio_data.xml'
    list_of_records = [
        "percentatge_acumulacio"
    ]
    load_data_records(
        cursor, 'som_facturacio_flux_solar', data_file, list_of_records, mode='update'
    )
    logger.info("XML records succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
