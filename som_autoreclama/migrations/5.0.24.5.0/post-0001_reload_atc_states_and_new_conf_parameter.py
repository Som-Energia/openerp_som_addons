# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Creating pooler")

    logger.info("Updating XML som_autoreclama_state_data.xml")
    load_data(
        cursor, 'som_autoreclama', 'data/som_autoreclama_state_data.xml', idref=None,
        mode='update'
    )
    logger.info("Create new config parameter at res_config_data.xml")
    load_data(
        cursor, 'som_autoreclama', 'data/res_config_data.xml', idref=None,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
