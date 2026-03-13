# -*- coding: utf-8 -*-
from __future__ import division
from ast import increment_lineno
from osv import osv, fields
from tools.translate import _
import time, json

class WizardFacturesLiquidacioInteressos(osv.osv_memory):
    """Assistent per liquidar els interessos.
    """
    _name = 'wizard.factures.liquidacio.interessos'
    _columns = {
        'date_invoice': fields.date(
            'Data factura'
        ),
        'date_start': fields.date(
            'Data inici',
            required=True
        ),
        'date_end': fields.date(
            'Data final',
            required=True
        ),
        'interest_rate': fields.float(
            'Interès anual (%)',
            required=True,
            help=u'El valor d\'aquest camp està definit amb una variable de configuració (som_aportacions_interest)'
        ),
        'err': fields.text(
            'Missatges d\'error',
            readonly=True,
        ),
        'calc': fields.text(
            'Missatges de càlcul',
            readonly=True,
        ),
        'state': fields.char(
            'Estat',
            50
        ),
        'res_ids': fields.json("Llistat de factures"),
        'open_invoices': fields.boolean(
            'Obrir factures, afegir a remesa i notificar per correu.',
            help="Marca aquesta opció per obrir les factures, afegir-les a la remesa i notificar per correu electronic.")
    }

    def _default_currrent_interest(self, cursor, uid, context=None):
        if not context:
            context = {}
        conf_obj = self.pool.get('res.config')
        interest_rate = conf_obj.get(cursor, uid, 'som_aportacions_interest', 0)
        return float(interest_rate)

    _defaults = {
        'res_ids': [],
        'state': lambda *a: 'init',
        'interest_rate': _default_currrent_interest,
        'date_invoice': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'date_start': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'date_end': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'open_invoices': lambda *a: False,
    }

    def create_invoice(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        Investment = self.pool.get('generationkwh.investment')
        Emission = self.pool.get('generationkwh.emission')

        from_list = context.get('from_list', 'all_items')

        wiz = self.browse(cursor, uid, ids[0], context=context)

        if 'selected_items' in from_list:
            investments_ids = context.get('active_ids', [])
            investments = Investment.browse(cursor, uid, investments_ids)
            all_emissions_in_selection = set([item.emission_id.type for item in investments])
            if any(item != 'apo' for item in all_emissions_in_selection):
                error_msg = _(u'Aquesta acció només es pot aplicar sobre'
                ' aportacions al capital social.')
                raise osv.except_osv(_(u'Error !'), error_msg)
        elif 'all_items' in from_list:
            apos_emission = Emission.search(cursor, uid, [('type','=','apo')])
            search_params = [
                ('emission_id', 'in', apos_emission),
                ('purchase_date', '<=', wiz.date_end),
                '|', ('last_effective_date', '=', False), ('last_effective_date', '>=', wiz.date_start),
                ('active', '=', True)
            ]
            investments_ids = Investment.search(cursor, uid, search_params)

        inv_obj = self.pool.get('generationkwh.investment')

        vals = {
            'date_invoice': wiz.date_invoice,
            'interest_rate': wiz.interest_rate,
            'date_start': wiz.date_start,
            'date_end': wiz.date_end,
        }

        context.update({'open_invoices': bool(wiz.open_invoices)})
        invoice_ids, errors = inv_obj.interest(cursor, uid, investments_ids, vals, context=context)

        errors = '\n'.join(errors)
        self.write(cursor, uid, [ids[0]],
            {'state': 'all_apos_calc',
             'res_ids': invoice_ids,
            'calc': 'Inversions sel·leccionades: {}\nFactures creades: {}\nErrors trobats de les factures no creades:\n{}'.format(
            len(investments_ids), len(invoice_ids), errors
        )})

    def _factures_apos(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        res_ids = wiz.res_ids
        return {
                'domain': "[('id','in',{})]".format(res_ids),
                'name': _('Factures Aportacions'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window'
            }

WizardFacturesLiquidacioInteressos()
