# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Creating cron to cancel draft policies older than three months")
    load_data_records(
        cursor,
        "som_polissa",
        "data/som_polissa_data.xml",
        ["ir_cron_cancel_draft_polisses"],
        mode="update",
    )


def down(cursor, installed_version):
    pass


migrate = up
