# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML files")
    list_of_records = [
        "som_environmental_impact_data",
        "mitjana_environmental_impact_data",
        "component_gdo_data",
    ]
    load_data_records(
        cursor,
        'giscedata_facturacio_comer_som',
        'giscedata_facturacio_comer_data.xml',
        list_of_records,
        mode='update'
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
