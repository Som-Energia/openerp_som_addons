# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import delete_record


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Removing tree view records")

    list_of_records = ["view_giscedata_facturacio_factura_generacio_som_form",
                       "view_giscedata_facturacio_factura_generacio_grouped_som_form"]
    delete_record(
        cursor,
        'som_facturacio_comer',
        list_of_records,
    )
    logger.info("Tree records successfully removed.")


def down(cursor, installed_version):
    pass


migrate = up
