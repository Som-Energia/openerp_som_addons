# coding=utf-8

import logging
import pooler
from datetime import date, timedelta
from tqdm import tqdm


def cercar_act_r1_006_polissa(cursor, uid, pol_id):
    pool = pooler.get_pool(cursor.dbname)
    atc_obj = pool.get("giscedata.atc")
    subtr_obj = pool.get("giscedata.subtipus.reclamacio")
    subtr_id = subtr_obj.search(cursor, uid, [("name", "=", "006")])[0]
    search_params = [
        ("state", "in", ['open', 'pending', 'done']),
        ("polissa_id", "=", pol_id),
        ("subtipus_id", "=", subtr_id),
    ]

    atc_ids = atc_obj.search(cursor, uid, search_params, order='id desc')
    if atc_ids:
        return atc_ids[0]
    return False


def up(cursor, installed_version):
    if not installed_version:
        return

    uid = 1
    pool = pooler.get_pool(cursor.dbname)

    logger = logging.getLogger("openerp.migration")
    logger.info("Assignar estat inicial a som autoreclama history state pòlissa a correcte")

    imd_obj = pool.get("ir.model.data")
    correct_state_id = imd_obj.get_object_reference(
        cursor, uid, "som_autoreclama", "correct_state_workflow_polissa"
    )[1]
    loop_state_id = imd_obj.get_object_reference(
        cursor, uid, "som_autoreclama", "loop_state_workflow_polissa"
    )[1]

    pol_obj = pool.get("giscedata.polissa")
    polh_obj = pool.get("som.autoreclama.state.history.polissa")

    search_params = [
        ("state", "in", ['activa', 'baixa', 'impagament', 'modcontractual']),
    ]

    baixa_year_ago = 0
    baixa_factura_ok = 0
    has_autoreclama = 0
    assigant_correct = 0
    assignat_loop = 0

    pol_ids = pol_obj.search(cursor, uid, search_params, context={'active_test': False})
    for pol_id in tqdm(pol_ids):
        pol = pol_obj.browse(cursor, uid, pol_id)

        date_one_year_ago = (date.today() - timedelta(days=300)).strftime("%Y-%m-%d")
        if pol.state == 'baixa' and pol.data_baixa <= date_one_year_ago:
            baixa_year_ago += 1
            continue

        if pol.state == 'baixa' and pol.data_baixa <= pol.data_ultima_lectura_f1:
            baixa_factura_ok +=1
            continue

        if pol.autoreclama_state:
            has_autoreclama += 1
            continue

        atc_006_id = cercar_act_r1_006_polissa(cursor, uid, pol_id)
        if atc_006_id:
            polh_obj.historize(cursor, uid, pol_id, loop_state_id, None, atc_006_id)
            assignat_loop += 1
        else:
            polh_obj.historize(cursor, uid, pol_id, correct_state_id, None, False)
            assigant_correct += 1

    logger.info("Resum assignacions")
    logger.info("> Baixa més d'un any --> {}".format(baixa_year_ago))
    logger.info("> Baixa tot facturat ---> {}".format(baixa_factura_ok))
    logger.info("> Ja té autoreclama --> {}".format(has_autoreclama))
    logger.info("> Assignat estat bucle --> {}".format(assignat_loop))
    logger.info("> Assignat estat correcte --> {}".format(assigant_correct))
    
    logger.info("Estats inicials per les giscedata_polissa creats")


def down(cursor, installed_version):
    pass


migrate = up
