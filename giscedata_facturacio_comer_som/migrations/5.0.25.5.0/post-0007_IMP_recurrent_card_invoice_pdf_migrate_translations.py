# -*- coding: utf-8 -*-
import logging
from tools.translate import trans_load
from tools import config


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating translations")
    trans_load(cursor, "{}/{}/i18n/es_ES.po".format(config['addons_path'], "giscedata_facturacio_comer_som"), 'es_ES')  # noqa: E501
    logger.info("Translations succesfully updated.")
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
