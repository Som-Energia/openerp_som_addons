# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pooler

from oopgrade.oopgrade import load_data
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return
    pool = pooler.get_pool(cursor.dbname)
    for model in (
        "wizard.reassign.move.analytics", "wizard.reassign.move.analytics.line",
    ):
        pool.get(model)._auto_init(
            cursor, context={"module": "account_analytic_som"}
        )
    for path in (
        "wizard/wizard_reassign_move_analytics_view.xml",
        "security/ir.model.access.csv",
    ):
        load_data(cursor, "account_analytic_som", path, idref=None, mode="update")


def down(cursor, installed_version):
    pass


migrate = up
