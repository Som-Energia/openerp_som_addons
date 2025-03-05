# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Creating new fields on wizard validate d101")
    pool.get("wizard.validate.d101")._auto_init(
        cursor, context={'module': 'som_switching'}
    )
    logger.info("Fields created successfully")

    # UPDATAR UN XML SENCER#
    logger.info("Updating XML wizard_validate_d101.xml")
    load_data(
        cursor,
        "som_switching",
        "wizard/wizard_validate_d101.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
