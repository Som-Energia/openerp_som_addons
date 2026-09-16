# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Moving member fee data XML IDs to som_partner_account")
    pool = pooler.get_pool(cursor.dbname)
    model_data_o = pool.get("ir.model.data")
    journal_o = pool.get("account.journal")

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

    journal_xml_id = model_data_o.search(
        cursor, 1,
        [("module", "=", "som_partner_account"),
         ("name", "=", "member_fee_journal")]
    )
    if not journal_xml_id:
        journal_ids = journal_o.search(cursor, 1, [("code", "=", "SOCIS")])
        if len(journal_ids) == 1:
            today = datetime.today().strftime("%Y-%m-%d")
            model_data_o.create(cursor, 1, {
                "noupdate": True,
                "name": "member_fee_journal",
                "module": "som_partner_account",
                "model": "account.journal",
                "res_id": journal_ids[0],
                "date_init": today,
                "date_update": today,
            })


def down(cursor, installed_version):
    pass


migrate = up
