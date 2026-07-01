# -*- coding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info('Removing obsolete contract summary inherited view')

    cursor.execute(
        """
        SELECT id
        FROM ir_ui_view
        WHERE id IN (
            SELECT res_id
            FROM ir_model_data
            WHERE module = 'som_polissa_condicions_generals'
              AND name = 'view_polisses_form_contract_summary'
              AND model = 'ir.ui.view'
        )
        OR name = 'giscedata.polissa.form.contract.summary'
        """
    )
    view_ids = [row[0] for row in cursor.fetchall()]

    if not view_ids:
        logger.info('Obsolete contract summary inherited view already removed')
        return

    cursor.execute(
        "DELETE FROM ir_ui_view_sc WHERE view_id IN %s",
        (tuple(view_ids),)
    )
    cursor.execute(
        "DELETE FROM ir_model_data WHERE module = %s AND name = %s",
        ('som_polissa_condicions_generals', 'view_polisses_form_contract_summary')
    )
    cursor.execute(
        "DELETE FROM ir_ui_view WHERE id IN %s",
        (tuple(view_ids),)
    )

    logger.info('Removed obsolete contract summary inherited view ids: %s', view_ids)


def down(cursor, installed_version):
    pass


migrate = up
