# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Creating new fields on wizard baixa soci")
    pool.get("wizard.baixa.soci")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    logger.info("Fields created successfully")

    # UPDATAR UN XML SENCER#
    logger.info("Updating XML wizard_baixa_soci.xml")
    load_data(
        cursor,
        "som_generationkwh",
        "wizard/wizard_baixa_soci.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up