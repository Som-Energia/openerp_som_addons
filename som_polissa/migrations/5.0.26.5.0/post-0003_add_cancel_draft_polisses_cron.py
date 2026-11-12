# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from oopgrade.oopgrade import load_data_records
from pooler import get_pool


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    pool = get_pool(cursor.dbname)
    logger.info("Creating cron to cancel draft policies older than three months")
    load_data_records(
        cursor,
        "som_polissa",
        "data/som_polissa_data.xml",
        ["ir_cron_cancel_draft_polisses"],
        mode="update",
    )
    cron_obj = pool.get("ir.cron")
    cron_id = pool.get("ir.model.data").get_object_reference(
        cursor, 1, "som_polissa", "ir_cron_cancel_draft_polisses"
    )[1]
    cron_obj.write(cursor, 1, [cron_id], {"active": False})


def down(cursor, installed_version):
    pass


migrate = up
