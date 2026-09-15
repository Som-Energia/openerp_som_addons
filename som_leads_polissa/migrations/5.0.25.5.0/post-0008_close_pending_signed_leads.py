# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    cursor.execute("""
        UPDATE crm_case AS c
        SET state = 'done'
        FROM giscedata_crm_lead AS l
        JOIN giscedata_signatura_process AS sp ON sp.id = l.signature_process
        WHERE c.id = l.crm_id
          AND c.state = 'pending'
          AND l.polissa_id IS NOT NULL
          AND l.firmat IS TRUE
          AND sp.status = 'completed'
    """)
    logger.info('Closed %s signed leads with a linked contract.', cursor.rowcount)


def down(cursor, installed_version):
    pass


migrate = up
