# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data_records
from tools import config


def up(cursor, installed_version):
    if not installed_version:
        return

    try:
        if config.updating_all:
            return
    except Exception as e:
        pass

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    ##UPDATAR UNA PART DE L'XML (POSAR LA ID)##
    logger.info("Updating XMLs")
    list_of_records = [
        "view_giscedata_import_bateria_virtual_tree_inherit",
        "giscedata_facturacio_bateria_virtual.act_giscedata_import_bateria_virtual",
        "giscedata_facturacio_bateria_virtual.value_giscedata_import_bateria_virtual",
    ]
    load_data_records(
        cursor, 'som_facturacio_flux_solar', 'giscedata_bateria_virtual.xml', list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up