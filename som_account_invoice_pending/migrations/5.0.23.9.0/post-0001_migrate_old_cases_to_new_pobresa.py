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
    imd_obj = pool.get('ir.model.data')

    section_id = imd_obj.get_object_reference(
        cursor, 1, 'giscedata_facturacio_comer_bono_social',
        'crm_section_bono_social_consulta_pobresa'
    )[1]
    search_vals = [
        ("section", "=", section_id),
    ]
    crm_list = crm_obj.search(cursor, uid, search_vals)
    logger.info('Trobats {} crm.case de pobresa energètica'.format(len(crm_list)))

    for crm_id in crm_list:
        crm = crm_obj.read(cursor, uid, crm_id,
                           ['name', 'polissa_id', 'partner_id', 'description',
                            'state', 'date'])
        create_vals = {
            "name": crm['name'],
            "polissa_id": crm['polissa_id'],
            "partner_id": crm['partner_id'],
            "description": crm['description'],
            "state": crm['state'],
            "date": crm['date'],
            'section_id': section_id,
        }
        if crm['state'] == 'done':
            create_vals['state'] = 'open'

        scp_obj.create(cursor, uid, create_vals)

    logger.info('S\'han creat les consultes pobresa')


def down(cursor, installed_version):
    pass


migrate = up
