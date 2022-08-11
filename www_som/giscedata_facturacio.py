# -*- coding: utf-8 -*-
from osv import osv
from tools import cache
from ast import literal_eval

_WWW_TIPUS_FACTURA = {
     'ordinaria': 'ORDINARIA',
     'abonadora': 'ABONADORA',
     'rectificadora': 'RECTIFICADORA',
}

_WWW_ESTAT_PAGAMENT = {
    'pagada': 'PAGADA',
    'no_pagada': 'NO_PAGADA',
    'en_proces': 'EN_PROCES',
    'error': 'ERROR',
}

class GiscedataFacturacioFactura(osv.osv):

    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    def www_estat_pagament_ov(self, cursor, uid, inv_id):
        inv_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = inv_obj.browse(cursor, uid, inv_id)
        return self._www_estat_pagament_ov(cursor, uid, inv_data)
    
    def www_estat_pagament_ov(self, cursor, uid, ids, context=None):
        """
        1)Si té estat oberta i té estat pedent (Correcte): 'EN_PROCES' 
        2)Si té estat oberta i té estat pendent (llistat_NO_pagables): 'EN_PROCES'
        3)Si té estat oberta i forma part d'una agrupació: 'EN_PROCES'
        4)Si té estat oberta i el residual és diferent al amount_total: 'EN_PROCES'
        5)Si té estat oberta i té estat pedent que no pertany a (llistat_NO_pagables): 'NO_PAGADA'
        6)Si té estat realitzat i té estat pendent (llistat_Fraccionaments) 'EN_PROCES'
        7)Si té estat realitzat: 'PAGADA'
        8)Altrament: 'ERROR'
        """
        cfg = self.pool.get('res.config')
        if isinstance(ids, (list, tuple)):
            ids = ids[0]
        inv = self.browse(cursor, uid, ids, context)
        inv_state = inv.state
        inv_pstate = inv.pending_state.id
        inv_group = inv.group_move_id
        ps_correct = literal_eval(cfg.get(cursor, uid, 'cobraments_ps_correcte', '[]'))
        ps_fraccio = literal_eval(cfg.get(cursor, uid, 'cobraments_ps_fraccio', '[]'))
        ps_no_pagables = literal_eval(cfg.get(cursor, uid, 'cobraments_ps_no_pagable', '[]'))

        if inv_state == 'open':
            partial = inv.amount_total != inv.residual
            if inv_pstate in ps_correct + ps_no_pagables or inv_group or partial:
                return _WWW_ESTAT_PAGAMENT['en_proces']
            return _WWW_ESTAT_PAGAMENT['no_pagada']
        if inv_state == 'paid':
            if inv_pstate in ps_fraccio:
                return _WWW_ESTAT_PAGAMENT['en_proces']
            return _WWW_ESTAT_PAGAMENT['pagada']
        return _WWW_ESTAT_PAGAMENT['error']

    def _www_tipus_factura(self, invoice):
        invoice_types = {
            'N': _WWW_TIPUS_FACTURA['ordinaria'],
            'A': _WWW_TIPUS_FACTURA['abonadora'],
            'B': _WWW_TIPUS_FACTURA['abonadora'],
            'R': _WWW_TIPUS_FACTURA['rectificadora'],
        }
        if invoice.tipo_rectificadora in invoice_types:
            return invoice_types[invoice.tipo_rectificadora]
        return invoice_types['N']

    def www_ultimes_factures(self, cursor, uid, partner_vat):
        par_obj = self.pool.get('res.partner')
        inv_obj = self.pool.get('giscedata.facturacio.factura')

        par_ids = par_obj.search(
            cursor, uid, [
                ('vat', '=', partner_vat),
            ])

        if not par_ids:
            return []

        inv_ids = inv_obj.search(
            cursor, uid, [
                ('partner_id', 'in', par_ids),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'in', ['open', 'paid']),
            ])

        result = []
        for inv_id in inv_ids:
            inv_data = inv_obj.browse(cursor, uid, inv_id)
            inv_type = self._www_tipus_factura(inv_data)
            inv = {}
            inv['id'] = inv_data.id
            inv['polissa_id'] = inv_data.polissa_id.id
            inv['number'] = inv_data.number
            inv['date_invoice'] = inv_data.date_invoice
            if inv_type == _WWW_TIPUS_FACTURA['abonadora']:
                inv['amount_total'] = inv_data.amount_total * (-1.0)
            else:
                inv['amount_total'] = inv_data.amount_total
            inv['data_inici'] = inv_data.data_inici
            inv['data_final'] = inv_data.data_final
            inv['tipus'] = inv_type
            inv['estat_pagament'] = self.www_estat_pagament_ov(cursor, uid, inv_id)
            inv['enviat'] = inv_data.enviat
            inv['visible'] = inv_data.visible_ov
            result.append(inv)

        return result


GiscedataFacturacioFactura()
