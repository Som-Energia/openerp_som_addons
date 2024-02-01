# coding=utf-8

from gettext import dgettext
import logging
import pooler
from datetime import date, timedelta
from tqdm import tqdm

from oopgrade.oopgrade import load_data, load_data_records


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

    list_of_records = ["view_giscedata_polissa_cau_tree"]
    load_data_records(
        cursor, "som_polissa", "giscedata_polissa_view.xml", list_of_records, mode="update"
    )
    logger.info("giscedata_switching_data.xml successfully updated")


def down(cursor, installed_version):
    pass


migrate = up
