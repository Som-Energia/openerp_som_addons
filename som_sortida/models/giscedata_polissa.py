# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    _inherit = 'giscedata.polissa'
    _description = 'Estats d\'una pòlissa en el procés de sortida'

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
        'sense_socia_vinculada': fields.boolean(
            'Sense sòcia vinculada',
            help='Indica si la pòlissa no té sòcia vinculada o és una promocional',
        ),
    }

    def _get_initial_sortida_state(self, cr, uid, context=None):
        """Get the initial state for a new sortida."""
        state_id = self.pool.get('som.sortida.state').search(
            cr, uid, [('name', '=', 'Correcte')], limit=1, context=context
        )
        return state_id and state_id[0] or False

    def _get_no_socia_vinculada(self, cr, uid, ids, context=None):
        """Get the default value for 'sense_socia_vinculada'."""
        # TODO: Categoria
        nif_promocional = ['PROMOCIONAL']
        pol_data = self.read(cr, uid, ids, ['soci_nif'], context=context)
        if not pol_data:
            return True
        elif pol_data[0]['soci_nif'] in nif_promocional:
            return True
        return False

    _defaults = {
        'sortida_state_id': lambda self, cr, uid, context: self._get_initial_sortida_state(cr, uid, context),  # noqa: E501
        'sense_socia_vinculada': lambda self, cr, uid, ids, context: self._get_no_socia_vinculada(cr, uid, ids, context),  # noqa: E501
    }


GiscedataPolissa()
