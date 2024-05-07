# coding=utf-8
import logging
import pooler
import netsvc
logger = logging.getLogger('openerp.' + __name__)


def up(cursor, installed_version):
    if not installed_version:
        return
    uid = 1

    pool = pooler.get_pool(cursor.dbname)
    scp_obj = pool.get('som.consulta.pobresa')
    crm_obj = pool.get('crm.case')
    crmh_obj = pool.get('crm.case.history')
    imd_obj = pool.get('ir.model.data')

    section_id = imd_obj.get_object_reference(
        cursor, 1, 'giscedata_facturacio_comer_bono_social',
        'crm_section_bono_social_consulta_pobresa'
    )[1]
    search_vals = [
        ("section_id", "=", section_id),
    ]
    crm_list = crm_obj.search(cursor, uid, search_vals)
    logger.info('Trobats {} crm.case de pobresa energètica'.format(len(crm_list)))

    for crm_id in crm_list:
        crm = crm_obj.browse(cursor, uid, crm_id)
        create_vals = {
            "name": crm.name,
            "polissa_id": crm.polissa_id.id,
            "partner_id": crm.partner_id.id,
            "description": crm.description,
            "state": crm.state,
            "date": crm.date,
            'section_id': section_id,
        }
        if crm['state'] == 'done':
            create_vals['state'] = 'open'

        scp_id = scp_obj.create(cursor, uid, create_vals)

        nou_scp = scp_obj.browse(cursor, uid, scp_id)
        message = "Consulta creada per migració dels antics CRM (crm.cases) amb id {}".format(
            crm_id)
        for crm_history in crm.history_line:
            message += """
            ===========
            {} / ({})
            {}
            """.format(crm_history.user_id.name, crm_history.date, crm_history.description)

        write_vals = {
            "user_id": uid,
            "case_id": nou_scp.crm_id.id,
            "date": crm.date,
            "description": message
        }
        crmh_obj.create(cursor, uid, write_vals)

        # Creem el workflow si no està creat
        wf_service = netsvc.LocalService("workflow")
        cursor.execute("select id from wkf_instance where "
                       "res_type = 'crm.case' and res_id = %s",
                       (nou_scp.crm_id.id,))
        res = cursor.fetchall()
        if not res:
            wf_service.trg_create(uid, 'crm.case', nou_scp.crm_id.id, cursor)

    logger.info('S\'han creat les consultes pobresa')


def down(cursor, installed_version):
    pass


migrate = up
