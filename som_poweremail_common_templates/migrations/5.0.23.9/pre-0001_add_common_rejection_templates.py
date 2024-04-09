# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records
import pooler


# Bug [ids]: Copy delete_record from PR https://github.com/gisce/oopgrade/pull/32#issuecomment-2044624005 # noqa: E501
def delete_record(cursor, module_name, record_names):
    logger = logging.getLogger('openerp.migration')
    uid = 1
    pool = pooler.get_pool(cursor.dbname)
    for record_name in record_names:
        # Find by model = ir.ui.view, module = module & name = the view_id
        logger.info(" {}: Deleting record: {}".format(module_name, record_name))
        sql_model = """
            SELECT id, model, res_id
            FROM ir_model_data WHERE
            module = %(module_name)s
            AND name = %(record_name)s
        """
        params_model = {
            'module_name': module_name,
            'record_name': record_name
        }
        cursor.execute(sql_model, params_model)
        model_data_vs = cursor.dictfetchall()
        # It should have only one.
        if model_data_vs and len(model_data_vs) == 1:
            # Delete from model data.
            sql_model_del = """
                DELETE FROM ir_model_data WHERE id = %(model_data_id)s
            """
            params_model_del = {
                'model_data_id': model_data_vs['id']
            }
            cursor.execute(sql_model_del, params_model_del)

            model_o = pool.get(model_data_vs['model'])
            model_o.unlink(cursor, uid, model_data_vs['res_id'])
        elif model_data_vs and len(model_data_vs) > 1:
            raise Exception(
                "More than one record found for model %s" % (model_data_vs['model'])
            )


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XMLs")

    list_of_records = ["common_template_rejection_footer",
                       "common_template_rejection_text_ca",
                       "common_template_rejection_text_es"]
    delete_record(
        cursor,
        'som_poweremail_common_templates',
        list_of_records,
    )

    list_of_records = ["common_template_modi_rejection_text",
                       "common_template_rejection_text"]
    load_data_records(
        cursor,
        'som_poweremail_common_templates',
        'commontemplates_data.xml',
        list_of_records,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
