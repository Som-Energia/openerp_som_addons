# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields

class GiscedataPolissaTarifaPeriodes(osv.osv):
    """Periodes de les Tarifes."""
    _name = 'giscedata.polissa.tarifa.periodes'
    _inherit = 'giscedata.polissa.tarifa.periodes'

    _columns = {
        'product_gkwh_id': fields.many2one(
            'product.product', 'Generation kWh', ondelete='restrict'
        ),
    }

GiscedataPolissaTarifaPeriodes()


class GiscedataPolissa(osv.osv):

    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def get_polisses_from_assignments(self, cursor, uid, ids, context=None):
        """ ids és la llista de 'generationkwh.assignment' que han sigut modificats
        retorna una llista de ids de 'giscedata.polissa' per les quals cal modificar el càlcul"""

        assig_obj = self.pool.get('generationkwh.assignment')

        pol_ids = assig_obj.read(cursor, uid, ids, ['contract_id'])
        return [p['contract_id'][0] for p in pol_ids]

    def _ff_get_assignacio_gkwh(self, cursor, uid, ids, field_name, arg,
                              context=None):
        if not context:
            context = {}
        assig_obj = self.pool.get('generationkwh.assignment')
        res = dict.fromkeys(ids, False)

        for _id in ids:
            search_params = [('contract_id','=', _id)]
            assigment_id = assig_obj.search(cursor, uid, search_params, limit=1)
            res[_id] = len(assigment_id) > 0

        return res


    _columns = {
        'te_assignacio_gkwh': fields.function(
            _ff_get_assignacio_gkwh, method=True, type='boolean',
            string='Té assignacions GWKH', readonly=True, help="El contracte té assignacions de GKWH, sense tenir en compte la prioritat ni data fi.",
            store={'generationkwh.assignment': (
                get_polisses_from_assignments,
                ['contract_id'],
                10)
            }),
    }


GiscedataPolissa()
