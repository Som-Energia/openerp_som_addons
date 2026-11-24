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
    imd_ids = imd_obj.search(cursor, 1, [
        ('module', '=', 'som_polissa_condicions_generals'),
        ('model', '=', 'ir.ui.view'),
        ('name', 'in', [
            'giscedata_crm_leads_contract_summary_view',
            'giscedata_crm_leads_contract_summary_full_view',
        ]),
    ])
    view_data = imd_obj.read(cursor, 1, imd_ids, ['res_id'])
    view_ids = [view['res_id'] for view in view_data if view['res_id']]
    if view_ids:
        # Preserve inherited views and user shortcuts instead of deleting views.
        cursor.execute(
            'UPDATE ir_ui_view SET arch=%s WHERE id IN %s',
            ('<data/>', tuple(view_ids))
        )


def down(cursor, installed_version):
    pass


migrate = up
