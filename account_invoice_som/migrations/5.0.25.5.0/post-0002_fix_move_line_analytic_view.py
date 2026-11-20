# -*- coding: utf-8 -*-
from __future__ import absolute_import

from oopgrade.oopgrade import load_data_records
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    load_data_records(
        cursor,
        "account_invoice_som",
        "account_move_view.xml",
        ["view_move_form_analytic_default"],
        mode="update",
    )


def down(cursor, installed_version):
    pass


migrate = up
