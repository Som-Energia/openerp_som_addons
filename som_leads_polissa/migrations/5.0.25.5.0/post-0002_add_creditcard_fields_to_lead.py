# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler


def up(cursor, installed_version):
    logger = logging.getLogger('openerp.migration')

    logger.info("Adding credit card lead fields to giscedata_crm_lead")

    pool = pooler.get_pool(cursor.dbname)

    pool.get("giscedata.crm.lead")._auto_init(
        cursor, context={'module': 'som_leads_polissa'}
    )


def down(cursor, installed_version):
    pass


migrate = up
