# -*- coding: utf-8 -*-
from osv import osv

_WWW_TIPUS_FACTURA = {
    0: 'ORDINARIA',
    1: 'ABONADORA',
    2: 'RECTIFICADORA',
}

_WWW_ESTAT_PAGAMENT = {
    0: 'PAGADA',
    1: 'NO_PAGADA',
    2: 'EN_PROCES',
    3: 'ERROR',
}

_PENDING_STATE_DOING = [
    u'Correct',
    u'R1 RECLAMACIÓ'
]

_PENDING_STATE_WITH_GROUPMOVE = [
    u'1F DEVOLUCIÓ',
    u'3F DEVOL ÚLTIM AVÍS',
    u'6F TALL',
    u'7F ADVOCATS',
    u'7F CUR',
    u'PACTE FRACCIO',
    u'PACTE TRANSFER',
    u'POBRESA',
    u'R1 RECLAMACIÓ'
]


class GiscedataFacturacioFactura(osv.osv):

    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    def www_estat_pagament_ov(self, cursor, uid, inv_id):
        inv_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = inv_obj.browse(cursor, uid, inv_id)
        return self._www_estat_pagament_ov(inv_data)

    def _www_estat_pagament_ov(self, invoice):
        if invoice.state == 'open':
            if invoice.pending_state and \
               invoice.pending_state.name in _PENDING_STATE_DOING:
                return _WWW_ESTAT_PAGAMENT[2]
            return _WWW_ESTAT_PAGAMENT[1]
        if invoice.state == 'paid':
            if invoice.group_move_id and \
               invoice.pending_state and \
               invoice.pending_state.name in _PENDING_STATE_WITH_GROUPMOVE:
                return _WWW_ESTAT_PAGAMENT[2]
            return _WWW_ESTAT_PAGAMENT[0]
        return _WWW_ESTAT_PAGAMENT[3]

    def _www_tipus_factura(self, invoice):
        invoice_types = {
            'N': _WWW_TIPUS_FACTURA[0],
            'A': _WWW_TIPUS_FACTURA[1],
            'B': _WWW_TIPUS_FACTURA[1],
            'R': _WWW_TIPUS_FACTURA[2],
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
            if inv_type == _WWW_TIPUS_FACTURA[1]:
                inv['amount_total'] = inv_data.amount_total * (-1.0)
            else:
                inv['amount_total'] = inv_data.amount_total
            inv['data_inici'] = inv_data.data_inici
            inv['data_final'] = inv_data.data_final
            inv['tipus'] = inv_type
            inv['estat_pagament'] = self._www_estat_pagament_ov(inv_data)
            inv['enviat'] = inv_data.enviat
            inv['visible'] = inv_data.visible_ov
            result.append(inv)

        return result


GiscedataFacturacioFactura()
