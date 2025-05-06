# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    logger = logging.getLogger("openerp.migration")
    logger.info("Starting member fee journal account.journal semantic id creation migration script")
    pool = pooler.get_pool(cursor.dbname)

    model_data_o = pool.get("ir.model.data")
    journal_o = pool.get("account.journal")

    journal_ids = journal_o.search(cursor, 1, [("code", "=", "SOCIS")])
    if len(journal_ids) == 1:
        journal_id = journal_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            "noupdate": True,
            "name": "member_fee_journal",
            "module": "som_leads_polissa",
            "model": "account.journal",
            "res_id": journal_id,
            "date_init": today,
            "date_update": today,
        }

        model_data_o.create(cursor, 1, model_data_vals)

    logger.info(
        "Finishing member fee journal account.journal semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
