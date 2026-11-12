# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Updating wizard baixa soci")
    pool.get("wizard.baixa.soci")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    logger.info("Updated successfully")

    logger.info("Updating XMLs")
    xml_to_update = [
        "wizard/wizard_baixa_soci.xml",
        "som_generationkwh_data.xml",
    ]
    for xml_file in xml_to_update:
        load_data(
            cursor,
            "som_generationkwh",
            xml_file,
            idref=None,
            mode="update",
        )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
