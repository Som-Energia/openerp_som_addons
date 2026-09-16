# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Setting member fee journal view")
    pool = pooler.get_pool(cursor.dbname)
    model_data_o = pool.get("ir.model.data")
    journal_o = pool.get("account.journal")

    journal_id = model_data_o.get_object_reference(
        cursor, 1, "som_partner_account", "member_fee_journal"
    )[1]
    view_id = model_data_o.get_object_reference(
        cursor, 1, "som_partner_account", "member_fee_journal_view"
    )[1]
    journal_o.write(cursor, 1, [journal_id], {"view_id": view_id})


def down(cursor, installed_version):
    pass


migrate = up
