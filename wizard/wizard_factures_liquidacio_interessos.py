# -*- coding: utf-8 -*-
from __future__ import division
from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from calendar import isleap
import time, netsvc, pooler


class WizardFacturesLiquidacioInteressos(osv.osv_memory):
    """Assistent per liquidar els interessos.
    """
    _name = 'wizard.factures.liquidacio.interessos'
    _columns = {
        'account': fields.many2one(
            'account.account',
            'Compte a liquidar',
            help='Assignar la compte a liquidar. Si és la compta general '
                 'liquidarà tots els interessos de les comptes filles. Si '
                 'només es vol liquidar els interessos d\'un soci s\'ha '
                 'd\'assignar la compte específica.'
        ),
        'account_prefix': fields.char(
            'Prefix comptes',
            size=5,
            help=u'Selecciona els comptes a liquidar a partir del codi. Agafa '
                 u'tots els comptes que comencin pel prefix especificat. Només '
                 u'quan no s\'ha seleccionat un compte específic'
        ),
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
        'journal': fields.many2one(
            'account.journal',
            'Dirari per crear les factures',
            required=True
        ),
        'interes': fields.float(
            'Interès anual (%)',
            required=True,
            help=u'El valor d\'aquest camp està definit amb una variable de configuració (som_aportacions_interest)'
        ),
        'product': fields.many2one(
            'product.product',
            'Producte',
            required=True
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
        'force': fields.boolean(
            'Forçar',
            help="Forçar els que el balanç sigui 0 a calcular-lo igualment"
        )
    }

    def _get_currrent_interest(self, cursor, uid, context=None):
        if not context:
            context = {}
        conf_obj = self.pool.get('res.config')
        interes = conf_obj.get(cursor, uid, 'som_aportacions_interest', 0)

        return float(interes)

    _defaults = {
        'state': lambda *a: 'init',
        'force': lambda *a: 0,
        'interes': _get_currrent_interest,
        'date_invoice': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S')
    }

    def all_apos_calc(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        read_only = context.get('read_only', True)

        self.write(cursor, uid, [ids[0]],
                  {'state': 'all_apos_calc'})

    def members_selection_calc(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        read_only = context.get('read_only', True)

        self.write(cursor, uid, [ids[0]],
                   {'state': 'members_selection_calc'})

        """
        return {
            'domain': "[('id','in', %s)]" % str(inv_ids),
            'name': _('Factures generades'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window'
        }
        """
WizardFacturesLiquidacioInteressos()
