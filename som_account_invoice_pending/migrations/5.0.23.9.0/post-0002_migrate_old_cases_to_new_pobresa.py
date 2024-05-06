# coding=utf-8
import logging
import pooler
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
        write_vals = {
            "user_id": uid,
            "case_id": nou_scp.crm_id.id,
            "date": crm.date,
            "description": "Consulta creada per migració dels antics "
            "CRM cases a partir del cas (crm.case) amb id {}".format(crm_id)
        }
        crmh_obj.create(cursor, uid, write_vals)

    logger.info('S\'han creat les consultes pobresa')


def down(cursor, installed_version):
    pass


migrate = up
