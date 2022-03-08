# -*- coding: utf-8 -*-
from osv import osv


class SomAutoreclamaStateUpdater(osv.osv_memory):

    _name = 'som.autoreclama.state.updater'

    def get_cacs_to_update(self, cursor, uid, context=None):

        pass

    def state_updater(self, cursor, uid, context=None):

        if context is None:
            context = {}

        """
        cacs_ids = self.get_cacs_to_update(cursor,uid)


        inv_obj = self.pool.get('account.invoice')
        invoice_ids = self.get_invoices_to_update(cursor, uid)

        last_lines_by_invoice = inv_obj.get_current_pending_state_info(
            cursor, uid, invoice_ids
        )

        for invoice_id, history_values in last_lines_by_invoice.items():
            self.update_state(cursor, uid, invoice_id, history_values)
        """
        return True

SomAutoreclamaStateUpdater()
