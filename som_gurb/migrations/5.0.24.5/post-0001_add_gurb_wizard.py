# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    uid = 1
    pool = pooler.get_pool(cursor.dbname)
    logger.info("Creating pooler")

    # Update models
    pool.get('som.gurb.cups')._auto_init(cursor, context={'module': 'som_gurb'})
    pool.get('wizard.deactivate.gurb.cups')._auto_init(cursor, context={'module': 'som_gurb'})

    # Create initial workflows
    import netsvc
    sgc_obj = pool.get('som.gurb.cups')
    wf_service = netsvc.LocalService("workflow")
    cursor.execute("""
        SELECT id FROM som_gurb_cups
        WHERE id NOT IN (SELECT res_id FROM wkf_instance WHERE res_type = 'som.gurb.cups')
    """)
    list_gurb_cups_ids = [row[0] for row in cursor.fetchall()]
    list_gurb_cups = sgc_obj.browse(cursor, uid, list_gurb_cups_ids)

    for gurb_cups in list_gurb_cups:
        wf_service.trg_create(uid, 'som.gurb.cups', gurb_cups.id, cursor)
        gurb_cups.send_signal('button_create_cups')
        gurb_cups.send_signal('button_activate_cups')
        print sgc_obj.read(cursor, uid, gurb_cups.id, ['state'])

    # Update XMLs
    views = [
        'views/som_gurb_cups_view.xml',
        'views/som_gurb_view.xml',
        'wizard/wizard_deactivate_gurb_cups_view.xml',
        'workflow/som_gurb_cups_workflow.xml',
        'security/ir.model.access.csv',
    ]
    for view in views:
        # Actualitza els diferents records i vistes
        logger.info("Updating XML {}".format(view))
        load_data(cursor, 'som_gurb', view, idref=None, mode='update')
        logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
