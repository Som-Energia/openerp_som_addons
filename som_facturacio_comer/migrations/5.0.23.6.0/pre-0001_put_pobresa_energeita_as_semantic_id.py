# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    logger = logging.getLogger("openerp.migration")
    logger.info("Starting Pobresa Energetica semantic id creation migration script")
    pool = pooler.get_pool(cursor.dbname)

    model_data_obj = pool.get("ir.model.data")
    categ_obj = pool.get("giscedata.polissa.category")

    categ_ids = categ_obj.search(cursor, 1, [("name", "ilike", "%Pobresa Energ%")])
    if len(categ_ids) == 1:
        categ_id = categ_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            "noupdate": True,
            "name": "categ_pobresa_energetica",
            "module": "som_polissa",
            "model": "giscedata.polissa.category",
            "res_id": categ_id,
            "date_init": today,
            "date_update": today,
        }

        model_data_obj.create(cursor, 1, model_data_vals)

    logger.info("Finishing Pobresa Energetica semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
