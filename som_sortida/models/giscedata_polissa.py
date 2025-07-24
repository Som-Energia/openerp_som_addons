# -*- coding: utf-8 -*-
from osv import osv, fields
import json


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'
    _description = 'Estats d\'una pòlissa en el procés de sortida'

    def create(self, cr, uid, vals, context=None):
        if 'sortida_state_id' not in vals or not vals['sortida_state_id']:
            imd_obj = self.pool.get('ir.model.data')
            state_correcte_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state'
            )[1]
            state_sense_socia_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
            )[1]
            if vals.get('soci', False):
                vals['sortida_state_id'] = state_correcte_id
            else:
                vals['sortida_state_id'] = state_sense_socia_id

        return super(GiscedataPolissa, self).create(cr, uid, vals, context=context)

    def _get_initial_sortida_state(self, cr, uid, context=None):
        """Get the initial state for a new sortida."""
        imd_obj = self.pool.get('ir.model.data')
        state_id = imd_obj.get_object_reference(
            cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state'
        )[1]

        if state_id:
            return state_id
        else:
            return False

    def _get_socia_real_vinculada(self, cr, uid, ids, field_name, arg, context=None):
        """Get the default value for 'te_socia_real_vinculada'."""
        res = dict.fromkeys(ids, True)
        config_obj = self.pool.get('res.config')
        nifs_promocionals = config_obj.get(cr, uid, 'llista_nifs_socia_promocional', '[]')
        nifs_promocionals = json.loads(nifs_promocionals)
        pol_data = self.read(cr, uid, ids, ['soci', 'soci_nif'], context=context)

        for pol in pol_data:
            if not pol['soci'] or not pol['soci_nif']:
                res[pol['id']] = False
            elif pol['soci_nif'] in nifs_promocionals:
                res[pol['id']] = False
            else:
                res[pol['id']] = True
        return res

    def _get_en_process_de_sortida(self, cr, uid, ids, field_name, arg, context=None):
        """Check if the polissa is in process of sortida."""
        res = dict.fromkeys(ids, False)
        for polissa in self.browse(cr, uid, ids, context=context):
            if polissa.sortida_state_id \
                    and polissa.sortida_state_id.weight > 0 \
                    and polissa.sortida_state_id.weight < 70:
                res[polissa.id] = True
            else:
                res[polissa.id] = False
        return res

    _STORE_SOCIA_VINCULADA = {
        'giscedata.polissa': (lambda self, cr, uid, ids, c={}: ids, ['soci_nif', 'soci'], 20),
    }

    _STORE_PROCESS_DE_SORTIDA = {
        'giscedata.polissa': (lambda self, cr, uid, ids, c={}: ids, ['sortida_state_id'], 20),
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
        'te_socia_real_vinculada': fields.function(
            _get_socia_real_vinculada, method=True, string='Sòcia real vinculada',
            type="boolean", store=_STORE_SOCIA_VINCULADA,
            help="Indica si la pòlissa té sòcia real vinculada o és promocional",
        ),
        'en_process_de_sortida': fields.function(
            _get_en_process_de_sortida, method=True, string='En procés de sortida',
            type="boolean", store=_STORE_PROCESS_DE_SORTIDA,
            help="Indica si la pòlissa està en procés de sortida",
        ),
    }


GiscedataPolissa()
