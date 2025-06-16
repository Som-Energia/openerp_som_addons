# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler
from tqdm import tqdm


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Initializing new fields")
    pool.get("giscedata.switching")._auto_init(
        cursor, context={'module': 'som_switching'}
    )

    logger.info("Updating XML and CSV files")
    data_files = [
        'giscedata_switching_view.xml',
    ]

    for data_file in data_files:
        load_data(
            cursor, 'som_switching', data_file,
            idref=None, mode='update'
        )

    full_migrate = True
    if full_migrate:
        logger.info("Populate new stored field.")
        uid = 1
        atr_cases = ["m1", "d1"]
        pool = pooler.get_pool(cursor.dbname)

        logger.info("Search the 01 steps for {}".format(','.join(atr_cases)))
        sw_01_ids = set()
        for atr_case in atr_cases:
            p01_obj = pool.get('giscedata.switching.{}.01'.format(atr_case))
            cau_ids = p01_obj.search(cursor, uid, [('dades_cau', '!=', None)])
            for cau_id in tqdm(cau_ids, desc='searching at {}.01'.format(atr_case)):
                p01 = p01_obj.browse(cursor, uid, cau_id)
                for cau in p01.dades_cau:
                    if cau.collectiu:
                        sw_01_ids.add(p01.sw_id.id)
        logger.info("Found {} cases ids from 01's".format(len(sw_01_ids)))

        logger.info("Search the 05 steps for {}".format(','.join(atr_cases)))
        sw_05_ids = set()

        p05_obj = pool.get('giscedata.switching.m1.05')
        cau_ids = p05_obj.search(cursor, uid, [('dades_cau', '!=', None)])
        for cau_id in tqdm(cau_ids, desc='searching at m1.05'):
            p05 = p05_obj.browse(cursor, uid, cau_id)
            found = False
            for cau in p05.dades_cau:
                if cau.collectiu:
                    sw_05_ids.add(p05.sw_id.id)
                    found = True
            if not found and p05.sw_id.id in sw_01_ids:
                sw_01_ids.remove(p05.sw_id.id)
        logger.info("Found {} cases ids from 05's".format(len(sw_05_ids)))

        sw_ids = sorted(list(sw_01_ids | sw_05_ids))
        logger.info("Found {} cases ids to set to collective".format(len(sw_ids)))
        sw_obj = pool.get("giscedata.switching")
        sw_obj._store_set_values(cursor, uid, sw_ids, ['collectiu_atr'], {})

        logger.info("New stored field populated!.")


def down(cursor, installed_version):
    pass


migrate = up
