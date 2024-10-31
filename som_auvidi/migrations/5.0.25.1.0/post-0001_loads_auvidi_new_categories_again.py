# coding=utf-8
import logging

import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    uid = 1
    pool = pooler.get_pool(cursor.dbname)
    category_obj = pool.get('giscedata.polissa.category')
    logger = logging.getLogger('openerp.migration')

    logger.info("Loading XML with new AUVIDI categories")
    load_data(
        cursor, 'som_auvidi', 'giscedata_serveis_generacio_data.xml',
        idref=None, mode='init'
    )
    logger.info("XMLs succesfully loaded.")

    # Rename other categories
    category_ids = category_obj.search(cursor, uid, [('code', 'like', 'AVD%')])

    for category_id in category_ids:
        category_data = category_obj.read(cursor, uid, category_id, ['name', 'code'])
        category_name = category_data['name'].replace('AUVIDI', 'AUVI')
        category_code = category_data['code'].replace('AVD', 'AUVI')

        category_obj.write(cursor, uid, category_id, {
            'name': category_name,
            'cade': category_code,
        })

def down(cursor, installed_version):
    pass


migrate = up
