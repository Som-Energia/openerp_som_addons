# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    pool = pooler.get_pool(cursor.dbname)
    model_data_o = pool.get("ir.model.data")
    payment_mode_o = pool.get("payment.mode")
    creditor_code = "ES24000F55091367"
    model_data_ids = model_data_o.search(cursor, 1, [
        ("module", "=", "som_partner_account"),
        ("name", "=", "mode_pagament_socis_factura"),
        ("model", "=", "payment.mode"),
    ])

    if not model_data_ids:
        logger.warning("Member fee payment mode external ID was not found")
    else:
        payment_mode_id = model_data_o.read(
            cursor, 1, model_data_ids[0], ["res_id"]
        )["res_id"]
        if not payment_mode_o.search(cursor, 1, [(
                "id", "=", payment_mode_id)]):
            logger.warning("Member fee payment mode was not found")
        else:
            payment_mode = payment_mode_o.read(
                cursor, 1, payment_mode_id, ["sepa_creditor_code"]
            )

            if payment_mode["sepa_creditor_code"] == creditor_code:
                logger.info(
                    "Member fee payment mode already has the correct "
                    "SEPA creditor code"
                )
            else:
                logger.info("Fixing member fee SEPA creditor code")
                payment_mode_o.write(cursor, 1, [payment_mode_id], {
                    "sepa_creditor_code": creditor_code,
                })


def down(cursor, installed_version):
    pass


migrate = up
