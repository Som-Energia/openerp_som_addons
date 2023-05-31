# -*- coding: utf-8 -*-
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
    logger.info("Creating table: giscedata.bateria.virtual.origen")
    pool.get("giscedata.bateria.virtual.origen")._auto_init(cursor, context={'module': 'som_facturacio_comer'})
    logger.info("Table created succesfully.")

    ##UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA##
    logger.info("Creating table: giscedata.bateria.virtual.percentatges.acumulacio")
    pool.get("giscedata.bateria.virtual.percentatges.acumulacio")._auto_init(cursor, context={'module': 'som_facturacio_comer'})
    logger.info("Table created succesfully")

    ##UPATAR UN XML SENCER##
    logger.info("Updating XML som_facturacio_comer/giscedata_bateria_virtual_origen.xml")
    load_data(
        cursor, 'som_facturacio_comer', 'giscedata_bateria_virtual_origen.xml', idref=None, mode='update'
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Updating access CSV")
    load_data(
        cursor, 'giscedata_facturacio_switching', 'security/ir.model.access.csv', idref=None, mode='update'
    )
    logger.info("CSV succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
