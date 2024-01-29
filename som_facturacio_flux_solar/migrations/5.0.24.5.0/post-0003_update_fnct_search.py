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


def down(cursor, installed_version):
    pass


migrate = up