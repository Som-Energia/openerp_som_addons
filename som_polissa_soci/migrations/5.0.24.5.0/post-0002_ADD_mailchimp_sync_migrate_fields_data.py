# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    logger.info("Updating XML files")
    data_files = [
        'data/giscedata_facturacio_data.xml',
        'data/giscedata_polissa_category_data.xml',
        'data/giscedata_som_soci_data.xml',
        'data/res_partner_data.xml',
        'data/somenergia_soci_data.xml',
        'views/giscedata_facturacio_view.xml',
        'views/giscedata_polissa_view.xml',
        'views/res_partner_view.xml',
        'views/somenergia_soci_view.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_polissa_soci', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
