# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    pool = pooler.get_pool(cursor.dbname)
    wizard_obj = pool.get("wizard.cancel.draft.polisses")
    wizard_obj._auto_init(cursor, context={"module": "som_polissa"})

    logger.info("Creating the wizard to cancel old draft policies")
    for resource in [
        "wizard/wizard_cancel_draft_polisses_view.xml",
        "security/ir.model.access.csv",
    ]:
        load_data(cursor, "som_polissa", resource, idref=None, mode="update")


def down(cursor, installed_version):
    pass


migrate = up
