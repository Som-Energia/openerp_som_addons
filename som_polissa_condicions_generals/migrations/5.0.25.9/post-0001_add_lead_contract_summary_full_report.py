# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info('Creating lead combined contract summary report XML')
    load_data(
        cursor,
        'som_polissa_condicions_generals',
        'report/giscedata_crm_lead_contract_summary_full_report.xml',
        idref=None,
        mode='update'
    )
    load_data(
        cursor,
        'som_polissa_condicions_generals',
        'security/ir.model.access.csv',
        idref=None,
        mode='update'
    )
    _neutralize_removed_button_views(cursor)


def _neutralize_removed_button_views(cursor):
    pool = pooler.get_pool(cursor.dbname)
    imd_obj = pool.get('ir.model.data')
    view_ids = imd_obj.search(cursor, 1, [
        ('module', '=', 'som_polissa_condicions_generals'),
        ('model', '=', 'ir.ui.view'),
        ('name', 'in', [
            'giscedata_crm_leads_contract_summary_view',
            'giscedata_crm_leads_contract_summary_full_view',
        ]),
    ])
    if not view_ids:
        return

    view_data = imd_obj.read(cursor, 1, view_ids, ['res_id'])
    stale_view_ids = [row['res_id'] for row in view_data if row['res_id']]
    if stale_view_ids:
        cursor.execute(
            'UPDATE ir_ui_view SET arch=%s WHERE id IN %s',
            ('<data/>', tuple(stale_view_ids))
        )


def down(cursor, installed_version):
    pass


migrate = up
