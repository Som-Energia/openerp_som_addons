# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    # UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA
    logger.info("Creating table: giscedata.facturacio.contracte_lot")
    pool.get("giscedata.facturacio.contracte_lot")._auto_init(
        cursor, context={"module": "som_facturacio_comer"}
    )
    logger.info("Table created succesfully.")

    # UPATAR UN XML SENCER
    logger.info("Updating XML som_facturacio_comer/giscedata_facturacio_contracte_lot_view.xml")
    load_data(
        cursor,
        "som_facturacio_comer",
        "giscedata_facturacio_contracte_lot_view.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    # UPDATAR UNA PART DE L'XML (POSAR LA ID)
    logger.info("Updating XMLs")
    list_of_records = [
        "view_giscedata_facturacio_contracte_lot_som_tree",
        "view_facturacio_contracte_lot_tree_som",
    ]
    load_data_records(
        cursor,
        "som_facturacio_comer",
        "giscedata_facturacio_contracte_lot_view.xml",
        list_of_records,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Updating access CSV")
    load_data(
        cursor, "som_facturacio_comer", "security/ir.model.access.csv", idref=None, mode="update"
    )
    logger.info("CSV succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
