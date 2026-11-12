# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_access_rules_from_model_name


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Updating Permissions")
    models = ["model_som_indexada_webforms_helpers"]
    load_access_rules_from_model_name(cursor, "www_som", models)
    logger.info("Permissions succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
