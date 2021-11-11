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
        """ rep llista de assigmetns que han sigut modificats"""
        """ha de retornar un allista de ids de pòlisses per les quals cal modificar el càlcul"""

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
        'data_alta_autoconsum': fields.date('Data alta autoconsum'),
        'te_assignacio_gkwh': fields.function(
            _ff_get_assignacio_gkwh, method=True, type='boolean',
            string='Té assignacions GWKH', readonly=True, help="El contracte té assignacions de GKWH, sense tenir en compte la prioritat ni data fi.",
            store={'generationkwh.assignment': (
                get_polisses_from_assignments,
                ['contract_id'],
                10)
            }),
    }

    _defaults = {
        'data_alta_autoconsum': lambda *a: False,
    }

GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    """Modificació Contractual d'una Pòlissa."""
    _name = 'giscedata.polissa.modcontractual'
    _inherit = 'giscedata.polissa.modcontractual'


    def create(self, cursor, uid, vals, context=None):
        res = super(GiscedataPolissaModcontractual, self).create(cursor, uid, vals, context)
        self.update_data_alta_autoconsum(cursor, uid, res, context=context)
        return res

    def write(self, cursor, uid, ids, vals, context=None):
        res = super(GiscedataPolissaModcontractual, self).write(cursor, uid, ids, vals, context)
        self.update_data_alta_autoconsum(cursor, uid, ids, context=context)
        return res

    def update_data_alta_autoconsum(self, cursor, uid, mod_id, context=None):
        """Escriu la data d'alta de l'autoconsum a la polissa, si en té"""
        import pudb; pu.db

        polissa_obj = self.pool.get('giscedata.polissa')
        fields_to_read = ['autoconsumo', 'autoconsum_id', 'data_inici']

        modcon_info = self.read(cursor, uid, [mod_id], fields_to_read)[0]

        if modcon_info['autoconsumo'] != '00' or modcon_info['autoconsum_id']:

            polissa_id = self.browse(cursor, uid, mod_id).polissa_id.id

            pol_data_alta_autoconsum = polissa_obj.read(cursor, uid, polissa_id, ['data_alta_autoconsum'])
            if not pol_data_alta_autoconsum:
                polissa_obj.write(cursor, uid, [polissa_id],
                {'data_alta_autoconsum': modcon_info['data_inici']},
                context={'skip_cnt_llista_preu_compatible': True})

        return True
