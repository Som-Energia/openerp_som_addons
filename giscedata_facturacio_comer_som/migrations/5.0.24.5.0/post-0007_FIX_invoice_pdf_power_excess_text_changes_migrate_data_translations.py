# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
from tools.translate import trans_load
from tools import config


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML files")
    data_files = [
        'giscedata_facturacio_comer_data.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'giscedata_facturacio_comer_som', data_file,
            idref=None, mode='update'
        )
    logger.info("Updating translations")
    trans_load(cursor, "{}/{}/i18n/es_ES.po".format(config['addons_path'], "giscedata_facturacio_comer_som"), 'es_ES')  # noqa: E501
    logger.info("Translations succesfully updated.")
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
