# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from tools import config
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    module_name = 'som_card_payment'

    logger.info('Updating translations')
    for language in ('ca_ES', 'es_ES'):
        trans_load(
            cursor,
            '{}/{}/i18n/{}.po'.format(config['addons_path'], module_name, language),
            language
        )
    logger.info('Translations successfully updated.')


def down(cursor, installed_version):
    pass


migrate = up
