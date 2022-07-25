# coding=utf-8

from gettext import dgettext
import logging
import pooler
from datetime import date,timedelta
from tqdm import tqdm

date_format = "%Y-%m-%d"

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
    atch_obj = pool.get('som.autoreclama.state.history.atc')


    cut_date = (date.today() - timedelta(days=15)).strftime(date_format)
    search_params = [
        ('active','=',True),
        ('state','not in', ['cancel', 'done']),
        ('date','>',cut_date)
        ]

    atc_ids = atc_obj.search(cursor, uid, search_params)
    for atc_id in tqdm(atc_ids):
        atc_data = atc_obj.read(cursor, uid, atc_id,['autoreclama_state'])
        if not atc_data.get('autoreclama_state', False):
            atch_obj.historize(cursor, uid, atc_id, correct_state_id, None, False)

    logger.info("Estats inicials per els giscedata_atc actius creats")


def down(cursor, installed_version):
    pass


migrate = up