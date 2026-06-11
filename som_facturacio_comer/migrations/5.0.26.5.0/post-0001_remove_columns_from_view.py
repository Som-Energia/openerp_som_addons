# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("UPDATE views")
    records = ['view_giscedata_facturacio_contracte_lot_som_tree', 'view_giscedata_facturacio_contracte_lot_som_form']
    load_data_records(cursor, 'som_facturacio_comer', 'giscedata_crm_lead_validation_data.xml', records)
    logger.info("Views updated succesfully")


def down(cursor, installed_version):
    pass


migrate = up
