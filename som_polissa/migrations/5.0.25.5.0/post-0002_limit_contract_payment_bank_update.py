# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    # Only Python logic changes; no schema or data update is needed.
    # Previously changed bank accounts cannot be safely inferred or restored.
    logger = logging.getLogger("openerp.migration")
    logger.info(
        "Contract payment bank updates are now limited to the contract's "
        "invoice move lines. Restart ERP services to load the updated code."
    )


def down(cursor, installed_version):
    pass


migrate = up
