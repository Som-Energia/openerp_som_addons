# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    logger = logging.getLogger("openerp.migration")
    logger.info("Starting Contracte button semantic id creation migration script")
    pool = pooler.get_pool(cursor.dbname)

    model_data_obj = pool.get("ir.model.data")
    ir_values_obj = pool.get("ir.values")

    button_ids = ir_values_obj.search(cursor, 1, [("name", "=", "somenergia.polissa_m101")])
    if len(button_ids) == 1:
        button_id = button_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            "noupdate": False,
            "name": "value_report_contracte_m101",
            "module": "som_polissa_condicions_generals",
            "model": "giscedata.switching",
            "res_id": button_id,
            "date_init": today,
            "date_update": today,
        }

        model_data_obj.create(cursor, 1, model_data_vals)

    logger.info("Finishing Contracte button semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
