# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    case_obj = pooler.get_pool(cursor.dbname).get('crm.case')
    cursor.execute("""
        SELECT c.id
        FROM giscedata_crm_lead AS l
        JOIN giscedata_signatura_process AS sp ON sp.id = l.signature_process
        WHERE c.id = l.crm_id
          AND c.state = 'pending'
          AND l.polissa_id IS NOT NULL
          AND l.firmat IS TRUE
          AND sp.status = 'completed'
    """)
    case_ids = [row[0] for row in cursor.fetchall()]
    if case_ids:
        case_obj.case_close(cursor, 1, case_ids)
    logger.info('Closed %s signed leads with a linked contract.', len(case_ids))


def down(cursor, installed_version):
    pass


migrate = up
