# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pooler.get_pool(cursor.dbname)

    views = [
        'wizard/wizard_deactivate_gurb_cups.xml',
        'workflow/som_gurb_cups_workflow.xml',
        'views/som_gurb_cups_view.xml',
    ]

    for view in views:
        # Actualitza els diferents records i vistes
        logger.info("Updating XML {}".format(view))
        load_data(cursor, 'som_gurb', view, idref=None, mode='update')
        logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
