# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    pool = pooler.get_pool(cursor.dbname)

    logger.info("Creating table: refund.rectify.batch")
    pool.get("refund.rectify.batch")._auto_init(
        cursor, context={"module": "som_facturacio_switching"}
    )
    logger.info("Table created succesfully.")

    logger.info("Creating table: refund.rectify.batch.line")
    pool.get("refund.rectify.batch.line")._auto_init(
        cursor, context={"module": "som_facturacio_switching"}
    )
    logger.info("Table created succesfully.")

    logger.info("Creating table: wizard.refund.rectify.batch")
    pool.get("wizard.refund.rectify.batch")._auto_init(
        cursor, context={"module": "som_facturacio_switching"}
    )
    logger.info("Table created succesfully.")

    logger.info("Updating XML files")
    data_files = [
        'wizard/wizard_refund_rectify_from_origin_view.xml',
        'wizard/wizard_refund_rectify_batch_view.xml',
        'refund_rectify_batch_view.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_facturacio_switching', data_file,
            idref=None, mode='update'
        )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'som_facturacio_switching', security_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
