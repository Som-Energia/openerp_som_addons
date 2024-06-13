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
    att_obj = pool.get('ir.attachment')

    section_id = imd_obj.get_object_reference(
        cursor, 1, 'giscedata_facturacio_comer_bono_social',
        'crm_section_bono_social_consulta_pobresa'
    )[1]
    search_vals = [
        ("section_id", "=", section_id),
        ('state', 'in', ['pending', 'done'])
    ]
    crm_list = crm_obj.search(cursor, uid, search_vals)
    logger.info('Trobats {} crm.case de pobresa energètica'.format(len(crm_list)))

    for crm_id in crm_list:
        crm = crm_obj.browse(cursor, uid, crm_id)
        search_vals = [
            ("res_id", "=", crm_id),
            ("res_model", "=", "crm.case"),
        ]
        attachment_list = att_obj.search(cursor, uid, search_vals)

        scp_id = scp_obj.search(cursor, uid, [("name", "=", crm.name)])
        if scp_id:
            logger.info('Trobats {} attachments de pobresa energètica per la consulta {}.'.format(
                len(attachment_list), scp_id[0]))

        for att_id in attachment_list:
            if scp_id:
                att = att_obj.browse(cursor, uid, att_id)
                create_vals = {
                    "res_model": "som.consulta.pobresa",
                    "res_id": scp_id[0],
                    "name": att.name,
                    "datas_fname": att.datas_fname,
                }
                att_obj.create(cursor, uid, create_vals)
                logger.info('Creats {} attachments de pobresa energètica per la consulta {}.'.format(  # noqa: E501
                    len(attachment_list), scp_id[0]))

    logger.info('S\'han creat els adjunts')


def down(cursor, installed_version):
    pass


migrate = up
