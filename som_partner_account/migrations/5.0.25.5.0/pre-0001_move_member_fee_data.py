# -*- coding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Moving member fee data XML IDs to som_partner_account")
    cursor.execute("""
        UPDATE ir_model_data
        SET module = 'som_partner_account'
        WHERE module = 'som_leads_polissa'
          AND name IN (
              'member_fee_journal',
              'mode_pagament_socis_factura',
              'socia_member_fee_amount'
          )
    """)


def down(cursor, installed_version):
    pass


migrate = up
