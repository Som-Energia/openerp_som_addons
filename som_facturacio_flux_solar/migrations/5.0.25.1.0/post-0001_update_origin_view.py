# -*- encoding: utf-8 -*-
import logging

from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XMLs")
    list_of_records = [
        "view_giscedata_bateria_virtual_origen_percentatges",
    ]
    load_data_records(
        cursor, 'som_facturacio_flux_solar', 'giscedata_bateria_virtual_origen.xml',
        list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
