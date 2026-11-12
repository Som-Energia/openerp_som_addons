# -*- coding: utf-8 -*-
import logging
import pooler
from datetime import datetime


def up(cursor, installed_version):
    logger = logging.getLogger('openerp.migration')
    logger.info("The Webforms USER semantic ID creation migration script has started")

    pool = pooler.get_pool(cursor.dbname)

    model_data_obj = pool.get('ir.model.data')
    res_users_obj = pool.get('res.users')

    res_users_ids = res_users_obj.search(cursor, 1, [('login', '=', 'webforms')])
    if len(res_users_ids) == 1:
        res_user_id = res_users_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")

        model_data_vals = {
            'noupdate': True,
            'name': 'res_users_webforms',
            'module': 'base_extended_som',
            'model': 'res.users',
            'res_id': res_user_id,
            'date_init': today,
            'date_update': today,
        }

        model_data_obj.create(cursor, 1, model_data_vals)

    logger.info("The Webforms USER semantic ID creation migration script has finished")


def down(cursor, installed_version):
    pass


migrate = up
