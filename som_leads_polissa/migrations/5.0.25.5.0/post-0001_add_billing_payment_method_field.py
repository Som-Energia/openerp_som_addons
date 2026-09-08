# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler


def up(cursor, installed_version):
    logger = logging.getLogger('openerp.migration')

    logger.info("Adding billing_payment_method column to giscedata_crm_lead")

    pool = pooler.get_pool(cursor.dbname)

    pool.get("giscedata.crm.lead")._auto_init(
        cursor, context={'module': 'som_leads_polissa'}
    )

    cursor.execute(
        """
        UPDATE giscedata_crm_lead
        SET billing_payment_method = 'remesa'
        WHERE billing_payment_method IS NULL
        """
    )
    logger.info("billing_payment_method column added and initialized")


def down(cursor, installed_version):
    pass


migrate = up
