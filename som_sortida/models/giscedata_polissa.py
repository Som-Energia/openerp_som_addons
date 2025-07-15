# -*- coding: utf-8 -*-
from osv import osv, fields
import json


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'
    _description = 'Estats d\'una pòlissa en el procés de sortida'

    def _get_initial_sortida_state(self, cr, uid, context=None):
        """Get the initial state for a new sortida."""
        state_id = self.pool.get('som.sortida.state').search(
            cr, uid, [('name', '=', 'Correcte')], limit=1, context=context
        )
        return state_id and state_id[0] or False

    def _get_no_socia_vinculada(self, cr, uid, ids, field_name, arg, context=None):
        """Get the default value for 'sense_socia_vinculada'."""
        res = dict.fromkeys(ids, False)
        config_obj = self.pool.get('res.config')
        nifs_promocionals = config_obj.get(cr, uid, 'llista_nifs_socia_promocional', '[]')
        nifs_promocionals = json.loads(nifs_promocionals)
        pol_data = self.read(cr, uid, ids, ['soci', 'soci_nif'], context=context)

        for pol in pol_data:
            if not pol['soci'] or not pol['soci_nif']:
                res[pol['id']] = True
            elif pol['soci_nif'] in nifs_promocionals:
                res[pol['id']] = True
            else:
                res[pol['id']] = False
        return res

    _STORE_SOCIA_VINCULADA = {
        'giscedata.polissa': (lambda self, cr, uid, ids, c={}: ids, ['soci_nif', 'soci'], 20),
    }

    _columns = {
        'sortida_state_id': fields.many2one(
            'som.sortida.state',
            'Estat de sortida',
            help='Estat de la pòlissa sense sòcia en el procés de sortida a la COR',
        ),
        'sortida_history_ids': fields.one2many(
            'som.sortida.history',
            'polissa_id',
            'Historial de sortides',
            help='Historial de sortides relacionades amb aquesta pòlissa',
        ),
        'sense_socia_vinculada': fields.function(
            _get_no_socia_vinculada, method=True, string='Sense sòcia vinculada',
            type="boolean", store=_STORE_SOCIA_VINCULADA,
            help="Indica si la pòlissa no té sòcia vinculada o és una promocional"
        ),
    }

    _defaults = {
        'sortida_state_id': _get_initial_sortida_state,
    }


GiscedataPolissa()
