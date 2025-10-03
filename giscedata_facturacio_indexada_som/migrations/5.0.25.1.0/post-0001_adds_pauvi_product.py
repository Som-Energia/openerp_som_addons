# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML giscedata_facturacio_indexada_som_data.xml")
    load_data_records(
        cursor, 'giscedata_facturacio_indexada_som', 'giscedata_facturacio_indexada_som_data.xml',
        ['product_auvi_som'], mode='init'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up