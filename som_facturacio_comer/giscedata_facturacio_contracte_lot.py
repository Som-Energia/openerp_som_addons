# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields
from tools.translate import _
from gestionatr.defs import TABLA_113
from datetime import datetime
import re

TIPO_AUTOCONSUMO_SEL = [(ac[0], '[{}] - {}'.format(ac[0], ac[1])) for ac in TABLA_113]


class GiscedataFacturacioContracteLot(osv.osv):
    """Contracte Lot per comercialitzadora.
    """
    _name = 'giscedata.facturacio.contracte_lot'
    _inherit = 'giscedata.facturacio.contracte_lot'

    def _ff_total_incidencies(self, cr, uid, ids, name, args, context=None):
        """ Retorna nombre d'incidències en contracte_lot """
        res = dict.fromkeys(ids, 0)
        for id in ids:
            status = self.read(cr, uid, id, ['status'])['status']
            if status:
                r1 = re.findall(r"(\[[a-zA-Z]{1,2}[\d]{2,3}\])", status)
                res[id] = len(set(r1))
            else:
                res[id] = 0
        return res

    def _ff_date_invoice(self, cr, uid, ids, name, args, context=None):
        """ Retorna la data de les factures """
        res = dict.fromkeys(ids, False)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        for id in ids:
            contracte_lot_data = self.read(cr, uid, id, ['lot_id','polissa_id'])
            date_invoice = 0
            try:
                lot_id = contracte_lot_data['lot_id'][0]
                pol_id = contracte_lot_data['polissa_id'][0]
                fact_ids = fact_obj.search(cr, uid, [('lot_facturacio','=', lot_id), ('polissa_id','=', pol_id)])
                if fact_ids:
                    date_invoice = fact_obj.read(cr, uid, fact_ids[0],
                            ['date_invoice'])['date_invoice']
            except Exception:
                pass
            res[id] = date_invoice
        return res

    def _get_fact_origen(self, cr, uid, id, context=None):
        if isinstance(id, list):
            id = id[0]

        fact_obj = self.pool.get('giscedata.facturacio.factura')

        contracte_lot_data = self.read(cr, uid, id, ['lot_id', 'polissa_id'])
        lot_id = contracte_lot_data['lot_id'][0]
        pol_id = contracte_lot_data['polissa_id'][0]

        fact_ids = fact_obj.search(cr, uid,[('lot_facturacio','=', lot_id), ('polissa_id','=', pol_id)])

        if fact_ids:
            for fact_id in fact_ids:
                energy_readings_o = self.pool.get('giscedata.facturacio.lectures.energia')
                reading_origin_o = self.pool.get('giscedata.lectures.origen')

                energy_readings_f = ['tipus', 'name', 'factura_id','origen_id', 'ajust']
                dmn = [('factura_id', '=', fact_id)]

                energy_reading_vs = energy_readings_o.q(cr, uid).read(energy_readings_f).where(dmn)
                if not energy_reading_vs:
                    return 'Sense Lectures'
                for energy_reading_v in energy_reading_vs:
                    estimada_ids = reading_origin_o.search(cr, uid, [('codi', '=', '40')])
                    if energy_reading_v['origen_id'] in estimada_ids:
                        return 'Estimada'
            return 'Real'
        return 'Sense Factures'

    def _ff_consum_facturat(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 'Sense Factures')
        for id in ids:
            n_factures = self.read(cr, uid, id, ['n_factures'])['n_factures']
            if n_factures:
                origen = self._get_fact_origen(cr, uid, id)
                res[id] = origen
        return res

    def _ff_te_generation(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        for id in ids:
            contracte_lot_data = self.read(cr, uid, id, ['lot_id','polissa_id'])
            linies_generacio = None
            try:
                lot_id = contracte_lot_data['lot_id'][0]
                pol_id = contracte_lot_data['polissa_id'][0]
                fact_ids = fact_obj.search(cr, uid, [('lot_facturacio','=', lot_id), ('polissa_id','=', pol_id)])
                for fact_id in fact_ids:
                    te_generation = fact_obj.read(cr, uid, fact_id, ['is_gkwh'])['is_gkwh']
                    if te_generation:
                        res[id] = True
            except Exception:
                pass
        return res

    def _ff_gran_contracte(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        pcat_obj = self.pool.get('giscedata.polissa.category')
        pcat_ids = pcat_obj.search(cr, uid,[('name','=','Gran Contracte')])
        for id in ids:
            contracte_lot_data = self.browse(cr, uid, id)
            polissa_id = contracte_lot_data.polissa_id
            if pcat_ids and pcat_ids[0] in [x.id for x in polissa_id.category_id]:
                res[id] = True
        return res

    def _get_clots_from_polissa(self, cr, uid, ids, context=None):
        """ids són els ids de pòlisses que han canviat. Hem de retornar els ids de clot que cal recalcular"""
        cl_obj = self.pool.get('giscedata.facturacio.contracte_lot')
        return cl_obj.search(cr, uid,[('polissa_id', 'in', ids)])

    def _ff_data_final(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        for id in ids:
            contracte_lot_data = self.read(cr, uid, id, ['lot_id','polissa_id'])
            try:
                lot_id = contracte_lot_data['lot_id'][0]
                pol_id = contracte_lot_data['polissa_id'][0]
                fact_ids = fact_obj.search(cr, uid, [('lot_facturacio','=', lot_id), ('polissa_id','=', pol_id)])

                data_final = datetime.strptime('1970-01-30','%Y-%m-%d')
                for fact_id in fact_ids:
                    data_final_factura = fact_obj.read(cr, uid, fact_id, ['data_final'])['data_final']
                    if data_final_factura > data_final:
                        data_final = data_final_factura

                if(data_final.strftime("%d-%m-%Y") != '30-01-1970'):
                    res[id] = data_final

            except Exception:
                pass
        return res

    _columns = {
        'polissa_distribuidora': fields.related('polissa_id', 'distribuidora', type='many2one', relation='res.partner',
                                string='Distribuidora', readonly=True),
        'autoconsum': fields.related('polissa_id', 'autoconsumo', type='selection',
                               selection=TIPO_AUTOCONSUMO_SEL, string='Autoconsum', readonly=True),
        'tarifaATR': fields.related('polissa_id', 'tarifa', 'name',
                                type='char', string=_('Tarifa Accés'), readonly=True),
        'llista_preu': fields.related('polissa_id', 'llista_preu', 'name',
                                type='char', string=_('Tarifa Comercialitzadora'), readonly=True),
        'total_incidencies': fields.function(
                                _ff_total_incidencies,
                                string='Nombre total dincidencies',
                                type='integer', store=True, method=True),
        'date_invoice': fields.function(
                                _ff_date_invoice,
                                string='Data de la factura',
                                type='date', size=12, store=True, method=True),
        'consum_facturat': fields.function(
                                _ff_consum_facturat,
                                string='Origen consum facturat',
                                type='char', size=32, store=True, method=True),
        'data_alta_contracte': fields.related('polissa_id', 'data_alta', type='date',
                                string=_('Data alta contracte'), readonly=True),
        'data_ultima_lectura': fields.related('polissa_id', 'data_ultima_lectura', type='date',
                                string=_('Data ultima lectura real facturada'), readonly=True),
        'info_gestions_massives': fields.related('polissa_id', 'info_gestions_massives', type='text',
                                string=_('Gestions Massives'), readonly=True),
        'mode_facturacio': fields.related('polissa_id', 'facturacio_potencia', type='char',
                                string='Mode facturació', readonly=True),
        'canal_enviament': fields.related('polissa_id', 'enviament', type='char',
                                string='Canal enviament', readonly=True),
        'te_generation': fields.function(
                                _ff_te_generation,
                                string='Factura té generation',
                                type='boolean', store=True, method=True),
        'gran_contracte': fields.function(
                                _ff_gran_contracte, string='Gran Contract',
                                method=True, type='boolean',
                                store = {
                                    'giscedata.polissa': (
                                        _get_clots_from_polissa,
                                        ['category_id'],
                                        10
                                    ),
                                    'giscedata.facturacio.contracte_lot': (
                                        lambda self, cr, uid, ids, context=None: ids,
                                        ['polissa_id'],
                                        10
                                    )
                                }),
        'data_final': fields.function(
                                _ff_data_final, string='Data final factura',
                                type='date', method=True, store=True),
        'te_generation_polissa': fields.related('polissa_id', 'te_assignacio_gkwh', type='boolean', relation='giscedata.polissa',
                                string=_('Pòlissa té generation'), readonly=True),
        'data_alta_auto': fields.related('polissa_id', 'data_alta_autoconsum', type='date', relation='giscedata.polissa',
                                string=_('Data alta autoconsum'), readonly=True),
        'n_retrocedir_lot':fields.integer(string='Num retrocedir', help="Número de vegades que la pòlissa en el lot s'ha retrocedit de lot", readonly=True),
    }

    _defaults = {
        'total_incidencies': lambda *a: 0,
        'n_retrocedir_lot': lambda *a: 0,
    }


GiscedataFacturacioContracteLot()

