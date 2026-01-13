# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data, load_data_records
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("giscedata.atc")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )
    pool.get("giscedata.polissa")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )
    pool.get("som.autoreclama.state")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )
    pool.get("som.autoreclama.state.history.atc")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )
    pool.get("som.autoreclama.state.history.polissa")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )
    pool.get("som.autoreclama.state.history.polissa009")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )
    pool.get("som.autoreclama.state.workflow")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )
    pool.get("wizard.som.autoreclama.set.correct.state")._auto_init(
        cursor, context={'module': 'som_autoreclama'}
    )

    logger.info("Updating XML files")
    data_files = [
        'data/giscedata_atc_tag_data.xml',
        'data/som_autoreclama_state_data.xml',
        'views/giscedata_atc_view.xml',
        'views/giscedata_polissa_view.xml',
        'views/som_autoreclama_state_view.xml',
        'wizard/wizard_som_autoreclama_set_correct_state_view.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_autoreclama', data_file,
            idref=None, mode='update'
        )

    logger.info("Updating records from XML file")
    update_records = [
        'workflow_atc',
        'workflow_F1',
        'workflow_polissa',
        'review_state_workflow_polissa',
    ]
    load_data_records(
        cursor, 'som_autoreclama', 'data/som_autoreclama_state_data.xml',
        update_records,
        mode='update'
    )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'som_autoreclama', security_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
