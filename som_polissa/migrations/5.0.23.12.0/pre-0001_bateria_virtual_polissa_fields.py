# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data_records, column_exists, drop_columns
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Dropping columns bateria_activa and data_activacio_bateria from giscedata_polissa")
    if column_exists(cursor, "giscedata_polissa", "bateria_activa"):
        drop_columns(cursor, [("giscedata_polissa", "bateria_activa")])
    if column_exists(cursor, "giscedata_polissa", "data_activacio_bateria"):
        drop_columns(cursor, [("giscedata_polissa", "data_activacio_bateria")])
    logger.info("Dropping columns finished")

    logger.info("Update giscedata_polissa_view.xml")
    records = [
        "view_giscedata_polissa_cau_tree",
        "view_giscedata_polissa_form_inherit",
        "view_giscedata_polissa_tree_inherit",
    ]
    load_data_records(cursor, "som_polissa", "giscedata_polissa_view.xml", records)
    logger.info("End updating giscedata_polissa_view.xml")


def down(cursor, installed_version):
    pass


migrate = up
