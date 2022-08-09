# -*- coding: utf-8 -*-

from osv import osv, fields
from ooquery.expression import Field


class FacturacioExtra(osv.osv):

    _name = 'giscedata.facturacio.extra'
    _inherit = 'giscedata.facturacio.extra'
    _order = 'id desc'

    def _ff_has_last_invoice_search(self, cursor, uid, obj, field_name, arg, context=None):
        if not arg:
            return []
        else:
            fact_obj = self.pool.get('giscedata.facturacio.factura')
            pol_ids = self.q(cursor, uid).read(['polissa_id']).where([
                ('polissa_id.state', '=', 'baixa'),('amount_pending', '!=', 0),('polissa_id.active', '=', False)
            ])
            pol_ids = [x['polissa_id'] for x in pol_ids]
            pol_fact_ids = fact_obj.q(cursor, uid).read(['polissa_id']).where([
                ('polissa_id', 'in', pol_ids),
                ('polissa_id.state', '=', 'baixa'),
                ('polissa_id.active', '=', False),
                ('data_final', '=', Field('polissa_id.data_baixa')),
            ])
            pol_fact_ids = [x['polissa_id'] for x in pol_fact_ids]
            if arg[0][2]:
                res_ids = self.search(cursor, uid, [('polissa_id', 'in', pol_fact_ids)])
            else:
                res_ids = self.search(cursor, uid, [('polissa_id', 'not in', pol_fact_ids)])
            return [('id', 'in', res_ids)]

    def _ff_has_last_invoice(self, cursor, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        for id in ids:
            polissa_id = self.read(cursor, uid, id, ['polissa_id'])['polissa_id']
            fact_ids = fact_obj.q(cursor, uid).read(['id']).where([
                ('polissa_id', '=', polissa_id[0]),
                ('polissa_id.state', '=', 'baixa'),
                ('polissa_id.active', '=', False),
                ('data_final', '=', Field('polissa_id.data_baixa')),
                ])
            res[id] = bool(fact_ids)
        return res

    def _ff_is_invoiced_search(self, cursor, uid, obj, field_name, arg, context=None):
        if not arg:
            return []
        else:
            if arg[0][2]:
                res_ids = self.search(cursor, uid, [('factura_linia_ids', '!=', False)])
            else:
                res_ids = self.search(cursor, uid, [('factura_linia_ids', '=', False)])
            return [('id', 'in', res_ids)]

    def _ff_is_invoiced(self, cursor, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        for id in ids:
            factura_ids = self.read(cursor, uid, id, ['factura_linia_ids'])['factura_linia_ids']
            res[id] = bool(len(factura_ids))
        return res

    def _ff_data_invoiced_search(self, cursor, uid, obj, field_name, arg, context=None):
        if not arg:
            return []
        else:
            res_ids = []
            if arg[0][2]:
                cursor.execute('''
                SELECT DISTINCT ex.id FROM giscedata_facturacio_extra ex
                LEFT JOIN facturacio_extra_factura_rel rel on rel.extra_id = ex.id
                LEFT JOIN giscedata_facturacio_factura fact on fact.id = rel.factura_id
                LEFT JOIN account_invoice inv on inv.id = fact.invoice_id
                WHERE inv.date_invoice {} '{}'
                '''.format(arg[0][1], arg[0][2]))

                res_ids = cursor.fetchall()
            return [('id', 'in', res_ids)]

    def _ff_data_invoiced(self, cursor, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        for id in ids:
            fact_data = self.read(cursor, uid, id, ['factura_ids'])
            if fact_data.get('factura_ids', False) and len(fact_data['factura_ids']):
                fact_ids = fact_data['factura_ids']
                fact_ids.sort(reverse=True)
                data_fact = fact_obj.read(cursor, uid, fact_ids[0], ['date_invoice'])
                res[id] = data_fact.get('date_invoice', False)
        return res

    def _ff_origin_number_search(self, cursor, uid, obj, field_name, arg, context=None):
        if not arg:
            return []
        else:
            res_ids = []
            linia_extra_obj = self.pool.get('giscedata.facturacio.importacio.linia.extra')
            if arg[0][2]:
                origin_number = arg[0][2]
                extra_ids = linia_extra_obj.q(cursor, uid).read(['extra_id']).where(
                    [('linia_id.invoice_number_text', '=', origin_number)]
                )
                res_ids = [x['extra_id'] for x in extra_ids]
            return [('id', 'in', res_ids)]

    def _ff_origin_number(self, cursor, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        linia_obj = self.pool.get('giscedata.facturacio.importacio.linia')
        linia_extra_obj = self.pool.get('giscedata.facturacio.importacio.linia.extra')
        for id in ids:
            fact_number = False
            linia_id = linia_extra_obj.q(cursor, uid).read(['linia_id']).where([('extra_id', '=', id)])
            if len(linia_id) and linia_id[0].get('linia_id', False):
                linia_origen = linia_obj.read(cursor, uid, linia_id[0]['linia_id'], ['invoice_number_text'])
                if linia_origen:
                    fact_number = linia_origen.get('invoice_number_text', False)
            res[id] = fact_number
        return res

    def _ff_data_origen_search(self, cursor, uid, obj, field_name, arg, context=None):
        if not arg:
            return []
        else:
            res_ids = []
            if arg[0][2]:
                cursor.execute('''
                SELECT DISTINCT extra_id FROM giscedata_facturacio_importacio_linia_extra liex
                LEFT JOIN giscedata_facturacio_importacio_linia imli ON imli.id = liex.linia_id
                WHERE imli.create_date::DATE {} '{}'
                '''.format(arg[0][1], arg[0][2]))

                res_ids = cursor.fetchall()

            return [('id', 'in', res_ids)]

    def _ff_data_origen(self, cursor, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        linia_obj = self.pool.get('giscedata.facturacio.importacio.linia')
        linia_extra_obj = self.pool.get('giscedata.facturacio.importacio.linia.extra')
        for id in ids:
            data_carrega = False
            linia_id = linia_extra_obj.q(cursor, uid).read(['linia_id']).where([('extra_id', '=', id)])
            if len(linia_id) and linia_id[0].get('linia_id', False):
                linia_origen = linia_obj.read(cursor, uid, linia_id[0]['linia_id'], ['data_carrega'])
                if linia_origen:
                    data_carrega = linia_origen.get('data_carrega', False)
            res[id] = data_carrega
        return res

    _columns = {
        'has_last_invoice': fields.function(_ff_has_last_invoice, method=True, type='boolean',
                                            string="Té darrera factura", fnct_search=_ff_has_last_invoice_search,
                                            readonly=True),
        'data_baixa_polissa': fields.related('polissa_id', 'data_baixa', type='date',
                                            string='Data baixa pòlissa', readonly=True),
        'is_invoiced': fields.function(_ff_is_invoiced, method=True, type='boolean',
                                       string="Ja en factura", fnct_search=_ff_is_invoiced_search,
                                       readonly=True),
        'data_invoiced': fields.function(_ff_data_invoiced, type='date', method=True, string='Data factura',
                                       fnct_search=_ff_data_invoiced_search),
        'origin_invoice': fields.function(_ff_origin_number, type='char', size=30,
                                          method=True, string='Fitxer origen', fnct_search=_ff_origin_number_search),
        'data_origen': fields.function(_ff_data_origen, type='datetime', method=True, string='Data fitxer origen',
                                       fnct_search=_ff_data_origen_search),
    }


FacturacioExtra()

