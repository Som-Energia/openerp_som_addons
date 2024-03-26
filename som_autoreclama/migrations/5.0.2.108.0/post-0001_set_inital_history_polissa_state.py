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

    # do not execute, make the setup in phases, too many objects, see:
    # PR https://github.com/Som-Energia/somenergia-scripts/pull/86
    # PR https://github.com/Som-Energia/somenergia-scripts/pull/85
    # PR https://github.com/Som-Energia/somenergia-scripts/pull/84
    """
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

    baixa_year_ago = []
    baixa_factura_ok = []
    has_autoreclama = []
    assignat_correct = []
    assignat_loop = []
    assignat_correct_no_previa = []

    date_75_days_ago = (date.today() - timedelta(days=75)).strftime("%Y-%m-%d")
    date_one_year_ago = (date.today() - timedelta(days=300)).strftime("%Y-%m-%d")

    pol_ids = pol_obj.search(cursor, uid, search_params, context={'active_test': False})
    pol_datas = pol_obj.read(
        cursor, uid,
        pol_ids,
        ['state', 'name', 'data_baixa', 'autoreclama_state', 'data_ultima_lectura_f1']
    )

    for pol_data in tqdm(pol_datas):

        if pol_data['state'] == 'baixa' and pol_data['data_baixa'] <= date_one_year_ago:
            baixa_year_ago.append(pol_data)
            continue

        if pol_data['state'] == 'baixa' and pol_data['data_baixa'] <= pol_data['data_ultima_lectura_f1']:  # noqa: E501
            baixa_factura_ok.append(pol_data)
            continue

        if 'autoreclama_state' in pol_data and pol_data['autoreclama_state']:
            has_autoreclama.append(pol_data)
            continue

        if pol_data['data_ultima_lectura_f1'] >= date_75_days_ago:
            polh_obj.historize(cursor, uid, pol_data['id'], correct_state_id, None, False)
            assignat_correct.append(pol_data)
        else:
            atc_006_id = cercar_act_r1_006_polissa(cursor, uid, pol_data['id'])
            if atc_006_id:
                polh_obj.historize(cursor, uid, pol_data['id'], loop_state_id, None, atc_006_id)
                pol_data['reclama'] = atc_006_id
                assignat_loop.append(pol_data)
            else:
                polh_obj.historize(cursor, uid, pol_data['id'], correct_state_id, None, False)
                assignat_correct_no_previa.append(pol_data)

    logger.info("Resum assignacions")
    logger.info("> Baixa més d'un any ------> {}".format(len(baixa_year_ago)))
    logger.info("> Baixa tot facturat ------> {}".format(len(baixa_factura_ok)))
    logger.info("> Ja té autoreclama -------> {}".format(len(has_autoreclama)))
    logger.info("> Assignat estat correcte (polissa ok) -------------------------> {}".format(len(assignat_correct)))            # noqa: E501
    logger.info("> Assignat estat bucle (polissa no ok amb R1 006 previa) -------> {}".format(len(assignat_loop)))               # noqa: E501
    logger.info("> Assignat estat correcte (polissa no ok sense R1 006 previa) --> {}".format(len(assignat_correct_no_previa)))  # noqa: E501
    logger.info("Estats inicials per les giscedata_polissa creats")
    """

def down(cursor, installed_version):
    pass


migrate = up
