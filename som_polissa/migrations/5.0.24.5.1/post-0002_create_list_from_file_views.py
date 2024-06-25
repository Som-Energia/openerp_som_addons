# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    pooler.get_pool(cursor.dbname)

    logger.info("Updating XMLs")
    load_data_records(
        cursor, "som_polissa",
        "giscedata_polissa_view.xml",
        ["view_giscedata_polissa_list_from_file_tree"], mode="update"
    )
    logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
