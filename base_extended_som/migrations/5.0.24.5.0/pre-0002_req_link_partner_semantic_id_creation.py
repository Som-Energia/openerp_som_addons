# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    logger = logging.getLogger("openerp.migration")
    logger.info("Starting res_request_link res_partner semantic id creation migration script")
    pool = pooler.get_pool(cursor.dbname)

    model_data_o = pool.get("ir.model.data")
    rec_link_o = pool.get("res.request.link")

    rec_link_ids = rec_link_o.search(cursor, 1, [("object", "=", "res.partner")])
    if len(rec_link_ids) == 1:
        rec_link_id = rec_link_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            "noupdate": True,
            "name": "req_link_partner",
            "module": "base_extended_som",
            "model": "res.request.link",
            "res_id": rec_link_id,
            "date_init": today,
            "date_update": today,
        }

        model_data_o.create(cursor, 1, model_data_vals)

    logger.info("Finishing res_request_link res_partner semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
