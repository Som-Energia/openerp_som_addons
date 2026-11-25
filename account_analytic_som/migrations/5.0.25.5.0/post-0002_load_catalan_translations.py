# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from tools import config
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Updating account_analytic_som Catalan translations")
    trans_load(
        cursor,
        "{}/account_analytic_som/i18n/ca_ES.po".format(config["addons_path"]),
        "ca_ES",
    )
    logger.info("Catalan translations successfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
