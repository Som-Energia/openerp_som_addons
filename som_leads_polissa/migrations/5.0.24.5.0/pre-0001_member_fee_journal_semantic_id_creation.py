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

    jounral_ids = journal_o.search(cursor, 1, [("object", "=", "res.partner")])
    if len(jounral_ids) == 1:
        jounral_id = jounral_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            "noupdate": True,
            "name": "member_fee_journal",
            "module": "som_leads_polissa",
            "model": "account.journal",
            "res_id": jounral_id,
            "date_init": today,
            "date_update": today,
        }

        model_data_o.create(cursor, 1, model_data_vals)

    logger.info(
        "Finishing member fee journal account.journal semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
