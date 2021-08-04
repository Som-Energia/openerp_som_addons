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

    def create_invoice(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        wiz = self.browse(cursor, uid, ids[0], context=context)

        inv_obj = self.pool.get('generationkwh.investment')

        inv_ids, errors = inv_obj.interest(cursor, uid, wiz.date_invoice, wiz.interes, ids=context['active_ids'])
        self.write(cursor, uid, [ids[0]],
            {'state': 'all_apos_calc',
            'calc': 'Inversions sel·leccionades: {}\nFactures creades: {}\nErrors trobats de les factures no creades: {}'.format(
            len(context['active_ids']), len(inv_ids), errors
        )})

WizardFacturesLiquidacioInteressos()
