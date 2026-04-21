# coding=utf-8
import logging
from tqdm import tqdm

import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    gfil_obj = pool.get("giscedata.facturacio.importacio.linia")

    cursor.execute(
        """SELECT id FROM giscedata_facturacio_importacio_linia WHERE user_observations = ''""")
    results = cursor.dictfetchall()

    gfil_ids = [res['id'] for res in results]

    gfils = gfil_obj.read(cursor, 1, gfil_ids, ['user_observations'])

    for gfil in tqdm(gfils):
        gfil_obj.write(cursor, 1, gfil.get('id'), {
                       'user_observations': False})

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
