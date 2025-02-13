# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    uid = 1

    logger.info("Creating pooler")
    pooler.get_pool(cursor.dbname)
    pooler.get('som.gurb.cups')._auto_init(cursor, context={'module': 'som_gurb'})

    # Update states of all GurbCups to active
    sgc_obj = pooler.get('som.gurb.cups')
    list_to_update = sgc_obj.search(cursor, uid, [('state', '=', False)])
    for _id in list_to_update[:1]:
        activation_date = sgc_obj.read(cursor, uid, _id, ['start_date'])['start_date']
        sgc_obj.write(cursor, uid, _id, {'state': 'active', 'state_date': activation_date})

    views = [
        'wizard/wizard_deactivate_gurb_cups.xml',
        'workflow/som_gurb_cups_workflow.xml',
        'views/som_gurb_cups_view.xml',
    ]
    for view in views:
        # Actualitza els diferents records i vistes
        logger.info("Updating XML {}".format(view))
        load_data(cursor, 'som_gurb', view, idref=None, mode='update')
        logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
