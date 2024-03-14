# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XMLs")

    list_of_records = ["view_giscedata_polissa_autoconsum_form_inherit"]
    load_data_records(
        cursor, 'som_polissa', 'giscedata_polissa_view.xml', list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
