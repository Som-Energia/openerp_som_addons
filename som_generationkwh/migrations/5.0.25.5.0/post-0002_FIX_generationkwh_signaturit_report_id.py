# -*- coding: utf-8 -*-
import logging

from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info('Loading Generation kWh Signaturit report metadata')
    load_data(
        cursor, 'som_generationkwh', 'som_generationkwh_data.xml',
        idref=None, mode='update'
    )

    cursor.execute("""
        SELECT res_id
        FROM ir_model_data
        WHERE module = %s
          AND name = %s
          AND model = %s
    """, (
        'som_generationkwh',
        'report_generationkwh_signaturit_doc',
        'ir.actions.report.xml',
    ))
    row = cursor.fetchone()
    if not row:
        raise Exception(
            'Missing som_generationkwh.report_generationkwh_signaturit_doc'
        )

    report_id = row[0]
    cursor.execute("""
        UPDATE giscedata_signatura_documents
        SET report_id = %s
        WHERE report_id IS NULL
          AND model LIKE 'generationkwh.investment,%%'
    """, (report_id,))
    logger.info(
        'Updated %s Generation kWh signature documents with report_id %s',
        cursor.rowcount,
        report_id,
    )


def down(cursor, installed_version):
    pass


migrate = up
