# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date

from osv import osv, fields
from osv.expression import OOQuery
import logging

class AccountInvoicePendingHistory(osv.osv):
    _name = 'account.invoice.pending.history'
    _inherit = 'account.invoice.pending.history'

    _columns = {
        'powersms_id': fields.many2one(
            'powersms.smsbox', u'SMS', required=False
        ),
        'powersms_sent_date': fields.date(u'SMS sent date', readonly=True)
    }

AccountInvoicePendingHistory()

class GiscedataFacturacioFactura(osv.osv):
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'


    def powersms_create_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el powersms quan es creei un sms
        a partir d'una pòlisssa.
        """
        if context is None:
            context = {}

        hist_obj = self.pool.get('account.invoice.pending.history')
        pending_state_id = context.get('pending_state_id',False)
        origin_ids = context.get('ps_callback_origin_ids', {})
        for f_id in ids:
            inv_id = self.read(cursor, uid, f_id, ['invoice_id'])['invoice_id'][0]
            search_params = [('invoice_id','=',inv_id)]
            if pending_state_id:
                search_params.append(('pending_state_id', '=',pending_state_id))
            hist_id = hist_obj.search(cursor, uid, search_params)
            if hist_id:
                hist_id = hist_id[0]
                hist_obj.write(cursor, uid, hist_id, {'powersms_id': origin_ids.get(f_id, False)})
        return True

    def powersms_write_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el powersms quan es modifiqui un sms.
        """

        if context is None:
            context = {}

        if 'date_sms' in vals and 'folder' in vals:
            vals_w = {
                'powersms_sent_date': vals['date_sms'],
            }
            if vals['folder'] == 'sent':
                hist_obj = self.pool.get('account.invoice.pending.history')
                origin_ids = context.get('ps_callback_origin_ids', {})
                for f_id in ids:
                    inv_id = self.read(cursor, uid, f_id, ['invoice_id'])['invoice_id'][0]
                    sms_id = origin_ids.get(f_id, False)
                    if sms_id:
                        hist_id = hist_obj.search(cursor, uid, [
                            ('invoice_id', '=', inv_id),
                            ('powersms_id', '=', sms_id)
                        ])
                        if hist_id:
                            hist_obj.write(cursor, uid, hist_id, vals_w)
        return True


GiscedataFacturacioFactura()
