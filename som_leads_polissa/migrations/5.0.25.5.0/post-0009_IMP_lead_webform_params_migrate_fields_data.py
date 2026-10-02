# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from oopgrade.oopgrade import load_data
import pooler
from tools import config
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Adding lead_tag to giscedata.crm.lead")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("giscedata.crm.lead")._auto_init(
        cursor, context={'module': 'som_leads_polissa'}
    )

    logger.info("Loading campaign categories and updated lead view")
    data_files = [
        'data/campaign_category_data.xml',
        'views/giscedata_crm_lead_view.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor,
            'som_leads_polissa',
            data_file,
            idref=None,
            mode='update',
        )

    logger.info("Loading module translations")
    for lang in ("ca_ES", "en_US", "es_ES"):
        trans_load(
            cursor,
            "{}/{}/i18n/{}.po".format(
                config["addons_path"], "som_leads_polissa", lang
            ),
            lang,
        )

    logger.info("Lead webform params migration completed")


def down(cursor, installed_version):
    pass


migrate = up
