# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    logger = logging.getLogger("openerp.migration")
    logger.info("Starting Pricelist indexada peninsula semantic id creation migration script")
    pool = pooler.get_pool(cursor.dbname)

    model_data_obj = pool.get("ir.model.data")
    pricelist_obj = pool.get("product.pricelist")

    pricelist_ids = pricelist_obj.search(cursor, 1, [("name", "=", "Indexada Empresa Península")])
    if len(pricelist_ids) == 1:
        pricelist_id = pricelist_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            "noupdate": True,
            "name": "pricelist_indexada_empresa_peninsula_non_standard",
            "module": "som_indexada",
            "model": "product.pricelist",
            "res_id": pricelist_id,
            "date_init": today,
            "date_update": today,
        }

        model_data_obj.create(cursor, 1, model_data_vals)

    logger.info("Finishing Pricelist indexada peninsula semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
