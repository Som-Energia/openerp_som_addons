# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    logger = logging.getLogger("openerp.migration")
    logger.info("Starting business tariff semantic id creation migration script")

    pool = pooler.get_pool(cursor.dbname)

    model_data_obj = pool.get("ir.model.data")
    polissa_category_obj = pool.get("giscedata.polissa.category")

    polissa_category_ids = polissa_category_obj.search(cursor, 1, [("name", "=", "Tarifa Empresa")])
    if len(polissa_category_ids) == 1:
        polissa_category_id = polissa_category_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            "noupdate": True,
            "name": "categ_tarifa_empresa",
            "module": "som_polissa",
            "model": "giscedata.polissa.category",
            "res_id": polissa_category_id,
            "date_init": today,
            "date_update": today,
        }

        model_data_obj.create(cursor, 1, model_data_vals)

    logger.info("Finishing business tariff semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
