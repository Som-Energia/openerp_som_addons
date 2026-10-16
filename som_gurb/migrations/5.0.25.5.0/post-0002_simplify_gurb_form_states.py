# -*- coding: utf-8 -*-
import logging

import netsvc
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)
    uid = 1
    workflow_obj = pool.get('workflow')
    workflow_ids = workflow_obj.search(cursor, uid, [('osv', '=', 'som.gurb.cau')])
    activity_ids = pool.get('workflow.activity').search(
        cursor, uid, [('wkf_id', 'in', workflow_ids)]
    )
    transition_ids = pool.get('workflow.transition').search(
        cursor, uid, [('act_from', 'in', activity_ids)]
    )
    imd_obj = pool.get('ir.model.data')
    for model, record_ids in [
        ('workflow.transition', transition_ids),
        ('workflow.activity', activity_ids),
        ('workflow', workflow_ids),
    ]:
        if record_ids:
            imd_ids = imd_obj.search(cursor, uid, [
                ('model', '=', model), ('res_id', 'in', record_ids),
            ])
            imd_obj.unlink(cursor, uid, imd_ids)
    if workflow_ids:
        # Activities, transitions and running instances are deleted by cascade.
        workflow_obj.unlink(cursor, uid, workflow_ids)
    netsvc.LocalService('workflow').clear_cache(cursor, uid)

    pool.get('som.gurb.cau')._auto_init(cursor, context={'module': 'som_gurb'})
    # Preserve existing web availability; new CAUs default to closed.
    # Keep state_date: migration is not a manual opening of the form.
    cursor.execute("""
        UPDATE som_gurb_cau SET state = 'open'
        WHERE state IS NULL OR state NOT IN ('open', 'closed')
    """)
    load_data(cursor, 'som_gurb', 'views/som_gurb_cau_view.xml', idref={}, mode='update')
    logger.info('GURB CAU forms migrated; existing forms remain available.')


def down(cursor, installed_version):
    pass


migrate = up
