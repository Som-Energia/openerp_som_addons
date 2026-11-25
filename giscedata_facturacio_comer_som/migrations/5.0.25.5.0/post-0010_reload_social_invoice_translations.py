# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from addons import get_module_resource
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Reloading social invoice translations for scripts-only updates")
    translation_path = get_module_resource(
        'giscedata_facturacio_comer_som', 'i18n', 'es_ES.po',
    )
    trans_load(cursor, translation_path, 'es_ES')
    logger.info("Translations successfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
