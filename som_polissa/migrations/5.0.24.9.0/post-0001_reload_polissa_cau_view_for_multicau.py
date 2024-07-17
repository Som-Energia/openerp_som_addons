# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating view_giscedata_polissa_cau_tree view")
    data_records = ["view_giscedata_polissa_cau_tree"]
    load_data_records(
        cursor, 'som_polissa', 'giscedata_polissa_view.xml', data_records,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
