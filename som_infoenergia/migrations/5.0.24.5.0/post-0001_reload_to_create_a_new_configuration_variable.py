# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Creating pooler")

    # UPATAR UN XML SENCER##
    logger.info("Updating XML som_infoenergia_data.xml")
    load_data(
        cursor, 'som_infoenergia', 'som_infoenergia_data.xml', idref=None,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
