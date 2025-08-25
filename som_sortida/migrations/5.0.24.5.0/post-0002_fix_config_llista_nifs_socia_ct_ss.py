# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating config_llista_nifs_socia_ct_ss")
    load_data_records(cursor, 'som_sortida', 'data/som_sortida_data.xml',
                      ['config_llista_nifs_socia_ct_ss'], mode='update')
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
