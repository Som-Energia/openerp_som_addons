# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    ##UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA##
    logger.info("Creating table: giscedata.bateria.virtual")
    pool.get("giscedata.bateria.virtual")._auto_init(cursor, context={'module': 'som_facturacio_flux_solar'})
    logger.info("Table created succesfully.")

    ##UPDATAR UNA PART DE L'XML (POSAR LA ID)##
    logger.info("Updating XMLs")
    list_of_records = [
        "view_som_bateria_virtual_tree",
    ]
    load_data_records(
        cursor, 'som_facturacio_flux_solar', 'giscedata_bateria_virtual.xml', list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
