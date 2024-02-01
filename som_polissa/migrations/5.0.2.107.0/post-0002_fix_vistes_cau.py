# coding=utf-8

import logging
import pooler

from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    ##UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA##
    logger.info("Updating table table: giscedata.polissa")
    pool.get("giscedata.polissa")._auto_init(cursor, context={"module": "som_polissa"})
    logger.info("Table updated succesfully.")

    list_of_records = [
        "view_giscedata_polissa_cau_tree",
        "view_giscedata_polissa_form_inherit_page_auto",
    ]
    load_data_records(
        cursor, "som_polissa", "giscedata_polissa_view.xml", list_of_records, mode="update"
    )
    logger.info("giscedata_polissa_view.xml successfully updated")


def down(cursor, installed_version):
    pass


migrate = up
