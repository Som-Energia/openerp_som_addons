# -*- encoding: utf-8 -*-
import logging
import pooler
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

    pool.get("giscedata.bateria.virtual.resum.facturacio").init(cursor)
    ##UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA##
    logger.info("Creating table: giscedata.bateria.virtual.resum.facturacio")
    pool.get("giscedata.bateria.virtual.resum.facturacio")._auto_init(cursor, context={'module': 'som_facturacio_flux_solar'})
    logger.info("Table created succesfully.")


def down(cursor, installed_version):
    pass


migrate = up
