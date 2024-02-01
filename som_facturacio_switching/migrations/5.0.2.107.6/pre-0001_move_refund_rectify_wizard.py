# coding=utf-8
import logging


def up(cursor, installed_version):
    logger = logging.getLogger("openerp.migration")
    if not installed_version:
        logger.info("Migration 5.0.2.107.0 not running because not installed_version found")
        return

    logger.info("Move Wizard refund rectify from origin")

    update_query = """
        UPDATE ir_model_data
        SET module ='som_facturacio_switching'
        WHERE module = 'som_facturacio_comer'
        AND name in ('model_wizard_refund_rectify_from_origin', 'field_wizard_refund_rectify_from_origin_info',
         'field_wizard_refund_rectify_from_origin_report_file', 'field_wizard_refund_rectify_from_origin_state',
         'field_wizard_refund_rectify_from_origin_max_amount', 'field_wizard_refund_rectify_from_origin_email_template',
         'field_wizard_refund_rectify_from_origin_facts_generades', 'field_wizard_refund_rectify_from_origin_order',
         'field_wizard_refund_rectify_from_origin_open_invoices', 'field_wizard_refund_rectify_from_origin_send_mail',
         'access_wizard_refund_rectify_from_origin_rcwd', 'view_wizard_refund_rectify_from_origin',
         'action_wizard_refund_rectify_from_origin_from_f1_form', 'value_wizard_refund_rectify_from_origin_from_f1_form')
        """  # noqa: E501
    cursor.execute(update_query)
    logger.info("Wizard migrated")


def down(cursor, installed_version):
    pass


migrate = up
