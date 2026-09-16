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
    payment_mode_o = pool.get("payment.mode")

    journal_id = model_data_o.get_object_reference(
        cursor, 1, "som_partner_account", "member_fee_journal"
    )[1]
    view_id = model_data_o.get_object_reference(
        cursor, 1, "som_partner_account", "member_fee_journal_view"
    )[1]
    journal_o.write(cursor, 1, [journal_id], {"view_id": view_id})

    payment_mode_id = model_data_o.get_object_reference(
        cursor, 1, "som_partner_account", "mode_pagament_socis_factura"
    )[1]
    payment_mode_o.write(cursor, 1, [payment_mode_id], {
        "sepa_creditor_code": "ES10000B22350466",
    })


def down(cursor, installed_version):
    pass


migrate = up
