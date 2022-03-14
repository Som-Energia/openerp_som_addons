# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from giscedata_polissa.giscedata_polissa import CONTRACT_STATES
from base_extended.base_extended import MultiprocessBackground, NoDependency
from oorq.decorators import job, create_jobs_group
from autoworker import AutoWorker
import json, time



STATES = [
    ('init', 'Estat Inicial'),
    ('step', 'Estat Segon'),
    ('finished', 'Estat Final')
]
INVOICE_TYPES = [
    ('in_invoice', 'Factura de proveïdor'),
    ('in_refund', 'Factura de proveïdor (abonadora)'),
    ('out_invoice', 'Factura de client'),
    ('out_refund', 'Factura de client (abonadora)')
]
INVOICES_STATES = [
    ('draft', _('Esborrany')),
    ('open', _('Obertes')),
    ('paid', _('Realitzades')),
    ('cancel', _(u'Cancel·lades')),
    ('all', _('Totes'))
]


class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    @job(queue='add_invoices_to_remesa')
    def afegeix_a_remesa_async(self, cursor, uid, ids, order_id, context=None):
        self.afegeix_a_remesa(cursor, uid, ids, order_id, context=context)

AccountInvoice()


class WizardPaymentOrderAddInvoices(osv.osv_memory):
    _name = 'wizard.payment.order.add.invoices'

    def add_invoices_to_payment_order(self, cursor, uid, ids, context=None):

        if not context.get('active_id', False) or len(context.get('active_ids', False)) > 1:
            raise osv.except_osv(_('Error!'), _('S\'ha de seleccionar una remesa'))

        order_id = context.get('active_id')
        po_obj = self.pool.get('payment.order')
        inv_obj = self.pool.get('account.invoice')

        wiz = self.browse(cursor, uid, ids[0])
        search_params = []

        search_params_relation =  {
            'invoice_state': [('state', '=', wiz.invoice_state)],
            'init_date': [('data_alta', '>=', wiz.init_date)],
            'end_date': [('data_alta', '<=', wiz.end_date)],
            'invoice_type': [('type', '=', wiz.invoice_type)],
            'fiscal_position': [('fiscal_position', '=', wiz.fiscal_position.id)],
            'payment_type': [('payment_type','=', wiz.payment_type.id)],
            'pending_state_text': [('pending_state', 'like', '{}%'.format(wiz.pending_state_text))]
        }

        for field in search_params_relation.keys():
            if getattr(wiz, field):
                search_params += (search_params_relation[field])

        res_ids = inv_obj.search(cursor, uid, search_params)

        self.write(cursor, uid, [wiz.id], {
            'state':'step',
            'len_result': 'La cerca ha trobat {} resultats'.format(len(res_ids)),
            'total_facts_to_add': len(res_ids),
            'res_ids': res_ids
        })

    def add_invoices_with_limit(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0])

        self.write(cursor, uid, ids, {
            'len_result': 'La tasca s\'ha encuat de forma asíncrona',
            'state': 'finished',
        })

        self.async_add_invoices_with_limit(cursor, uid, ids, context)

    def async_add_invoices_with_limit(self, cursor, uid, ids, context=None):

        wiz = self.browse(cursor, uid, ids[0])
        inv_ids = wiz.res_ids
        order_id = wiz.order.id
        limit = wiz.total_facts_to_add

        order_obj = self.pool.get('payment.order')
        inv_obj = self.pool.get('account.invoice')
        oder = order_obj.browse(cursor, uid, order_id)
        jobs_ids = []
        with NoDependency():
            for inv_id in inv_ids:
                j = inv_obj.afegeix_a_remesa_async(cursor, uid, [inv_id], order_id,
                                                   context)
                jobs_ids.append(j.id)
        create_jobs_group(
            cursor.dbname, uid,
            _(u'Remesa {} - afegint {} factures a la remesa').format(
                oder.name, len(inv_ids)
            ), 'invoicing.add_invoices_to_remesa', jobs_ids
        )
        aw = AutoWorker(queue='add_invoices_to_remesa')
        aw.work()

    def _get_default_fiscal_position(self, cursor, uid, context):
        irmd_obj = self.pool.get('ir.model.data')
        default_id = irmd_obj.search(cursor, uid, [('name','=','fp_nacional_2012')])
        if default_id:
            return irmd_obj.browse(cursor, uid, default_id[0]).res_id
        return False

    _columns = {
        'state': fields.selection(STATES, _(u'Estat del wizard')),
        'order': fields.many2one('payment.order', 'Remesa', select=True),
        'len_result': fields.text('Resultat de la cerca', readonly=True),
        'total_facts_to_add': fields.integer(_('Num. de factures a incloure'),
            help='Numero de factures per afegir a la remesa'),
        'res_ids': fields.json("Dades d\'us per l\'assistent"),
        'pending_state_text': fields.char('Estat pendent', size=256),
        'init_date': fields.date(_('Data inici')),
        'end_date': fields.date(_('Data final')),
        'invoice_state': fields.selection([(False, '')]+INVOICES_STATES, _('Estat')),
        'invoice_type': fields.selection([(False, '')]+ INVOICE_TYPES, _('Tipus')),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Posició Fiscal'),
        'payment_type': fields.many2one('payment.type', 'Tipus de pagament'),
    }

    _defaults = {
        'state': 'init',
        'order': lambda self, cr, uid, context: context.get('active_id', False),
        'invoice_state': 'open',
        'init_date': lambda *a: time.strftime('%Y-%m-%d'),
        'end_date': lambda *a: time.strftime('%Y-%m-%d'),
        'invoice_type': 'out_invoice',
    }

WizardPaymentOrderAddInvoices()
