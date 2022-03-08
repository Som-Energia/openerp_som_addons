# coding=utf-8

from gettext import dgettext
import logging
import pooler
from datetime import date
from tqdm import tqdm

def up(cursor, installed_version):
    if not installed_version:
        return

    uid = 1
    pool = pooler.get_pool(cursor.dbname)

    logger = logging.getLogger('openerp.migration')
    logger.info(
        "Asignar estat inicial a som autoreclama history state atc a correcte"
    )

    imd_obj = pool.get('ir.model.data')
    correct_state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_autoreclama', 'correct_state_workflow_atc'
    )[1]

    atc_obj = pool.get('giscedata.atc')
    atch_obj = pool.get('som.autoreclama.pending.state.history.atc')
    search_params = [('active','=',True),('state','not in', ['cancel', 'done'])]
    atc_ids = atc_obj.search(cursor, uid, search_params)
    for atc_id in tqdm(atc_ids):
        atch_obj.create(
            cursor,
            uid,
            {
                'atc_id': atc_id,
                'autoreclama_state_id': correct_state_id,
                'change_date': date.today().strftime("%d-%m-%Y"),
            }
        )
    logger.info("Estats inicials per els giscedata_atc actius creats")


def down(cursor, installed_version):
    pass


migrate = up