# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records
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

    ##UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA##
    logger.info("Creating table: giscedata.facturacio.contracte_lot")
    pool.get("giscedata.facturacio.contracte_lot")._auto_init(cursor, context={'module': 'som_facturacio_comer'})
    logger.info("Table created succesfully.")

    ##UPDATAR UNA PART DE L'XML (POSAR LA ID)##
    logger.info("Updating XMLs")
    list_of_records = [
        "view_giscedata_facturacio_contracte_lot_som_tree",
    ]
    load_data_records(
        cursor, 'som_facturacio_comer', 'giscedata_facturacio_contracte_lot_view.xml', list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up