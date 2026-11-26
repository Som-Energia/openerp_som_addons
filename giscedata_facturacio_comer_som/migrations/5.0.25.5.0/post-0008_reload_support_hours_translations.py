# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from tools import config
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating support hours translations")
    translation_path = "{}/{}/i18n/es_ES.po".format(
        config['addons_path'], 'giscedata_facturacio_comer_som'
    )
    trans_load(cursor, translation_path, 'es_ES')
    logger.info("Translations successfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
