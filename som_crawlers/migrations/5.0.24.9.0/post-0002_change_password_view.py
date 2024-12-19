# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Updating XML")
    load_data(
        cursor, "som_crawlers", "views/som_crawlers_config_view.xml", mode="update"
    )
    logger.info("XML succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
