# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Initializing the social tariff checkbox")
    pool = pooler.get_pool(cursor.dbname)
    pool.get("wizard.massive.k.change")._auto_init(
        cursor, context={"module": "som_indexada"}
    )
    load_data_records(
        cursor, "som_indexada", "data/giscedata_polissa_category_data.xml",
        ["category_tarifa_social"], mode="update",
    )
    load_data_records(
        cursor, "som_indexada", "wizard/wizard_massive_k_change.xml",
        ["view_wizard_massive_k_change_form"], mode="update",
    )
    logger.info("Social tariff category and K-change view loaded")


def down(cursor, installed_version):
    pass


migrate = up
