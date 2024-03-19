# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    # UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA##
    logger.info("Creating table: giscedata.bateria.virtual")
    pool.get("giscedata.bateria.virtual")._auto_init(
        cursor, context={"module": "som_facturacio_flux_solar"}
    )
    logger.info("Table created succesfully.")

    logger.info("Creating table: giscedata.bateria.virtual.origen")
    pool.get("giscedata.bateria.virtual.origen")._auto_init(
        cursor, context={"module": "som_facturacio_flux_solar"}
    )
    logger.info("Table created succesfully.")

    logger.info("Creating table: giscedata.bateria.virtual.percentatges.acumulacio")
    pool.get("giscedata.bateria.virtual.percentatges.acumulacio")._auto_init(
        cursor, context={"module": "som_facturacio_flux_solar"}
    )
    logger.info("Table created succesfully.")

    # UPATAR UN XML SENCER##
    logger.info("Updating XML giscedata_bateria_virtual.xml")
    load_data(
        cursor,
        "som_facturacio_flux_solar",
        "giscedata_bateria_virtual.xml",
        idref=None,
        mode="update",
    )
    logger.info("Updating XML giscedata_bateria_virtual_origen.xml")
    load_data(
        cursor,
        "som_facturacio_flux_solar",
        "giscedata_bateria_virtual_origen.xml",
        idref=None,
        mode="update",
    )
    logger.info("Updating XML giscedata_bateria_virtual_percentatges_acumulacio_data.xml")
    load_data(
        cursor,
        "som_facturacio_flux_solar",
        "giscedata_bateria_virtual_percentatges_acumulacio_data.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
