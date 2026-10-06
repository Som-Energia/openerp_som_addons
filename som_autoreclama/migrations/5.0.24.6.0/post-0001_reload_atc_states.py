# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML som_autoreclama_state_data.xml")
    load_data_records(
        cursor, 'som_autoreclama', 'data/som_autoreclama_state_data.xml',
        [
            'review_state_workflow_polissa',
            'conditions_revisar_to_correct_state_workflow_polissa',
        ],
        mode='init'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
