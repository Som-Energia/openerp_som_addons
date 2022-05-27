# -*- coding: utf-8 -*-
from osv import osv
from tools import cache


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

class GiscedataFacturacioFactura(osv.osv):

    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    @cache(timeout=3600)
    def _pending_state_with_doing_by_id(self, cursor, uid):
        irmd_obj = self.pool.get('ir.model.data')

        pending_states = [
            # Correct bs i dp
            ('giscedata_facturacio_comer_bono_social', 'correct_bono_social_pending_state'),
            ('account_invoice_pending', 'default_invoice_pending_state'),
            # R1 Reclamació
            ('som_account_invoice_pending', 'reclamacio_en_curs_pending_state'),
            ('som_account_invoice_pending', 'default_reclamacio_en_curs_pending_state'),
        ]

        ps_list = []
        for module, name in pending_states:
            ps_id = irmd_obj.get_object_reference( cursor, uid, module, name)[1]
            if ps_id:
                ps_list.append(ps_id)
        return ps_list

    @cache(timeout=3600)
    def _pending_state_with_groupmove_by_id(self, cursor, uid):
        irmd_obj = self.pool.get('ir.model.data')

        pending_states = [
            # Impagaments bs i dp
            ('giscedata_facturacio_comer_bono_social', 'avis_impagament_pending_state'),
            ('som_account_invoice_pending', 'default_avis_impagament_pending_state'),
            # Darrer avís bs i dp
            ('som_account_invoice_pending', 'notificacio_tall_imminent_enviada_pending_state'),
            ('som_account_invoice_pending', 'default_pendent_notificacio_tall_imminent_pending_state'),
            # Tall bs i dp
            ('som_account_invoice_pending', 'default_tall_pending_state'),
            ('giscedata_facturacio_comer_bono_social','tall_pending_state'),
            # Advocats bs i dp
            ('som_account_invoice_pending', 'pendent_traspas_advocats_pending_state'),
            ('som_account_invoice_pending', 'default_pendent_traspas_advocats_pending_state'),
            ('som_account_invoice_pending', 'monitori_bo_social_pending_state'),
            ('som_account_invoice_pending', 'default_monitori_pending_state'),
            ('som_account_invoice_pending', 'pending_tugesto_bo_social_pending_state'),
            ('som_account_invoice_pending', 'pending_tugesto_default_pending_state'),
            ('som_account_invoice_pending', 'tugesto_bo_social_pending_state'),
            ('som_account_invoice_pending', 'tugesto_default_pending_state'),
            ('som_account_invoice_pending', 'traspassat_advocats_pending_state'),
            ('som_account_invoice_pending', 'default_traspassat_advocats_pending_state'),
            # Fraccionament bs i dp
            ('som_account_invoice_pending', 'pacte_fraccio_pending_state'),
            ('som_account_invoice_pending', 'default_pacte_fraccio_pending_state'),
            ('som_account_invoice_pending', 'fracc_manual_bo_social_pending_state'),
            ('som_account_invoice_pending', 'fracc_manual_default_pending_state'),
            # Pacte transfer bs i dp
            ('som_account_invoice_pending', 'pacte_transferencia_pending_state'),
            ('som_account_invoice_pending', 'default_pacte_transferencia_pending_state'),
            # Pobresa bs
            ('som_account_invoice_pending', 'probresa_energetica_certificada_pending_state'),
            # R1 Reclamació
            ('som_account_invoice_pending', 'reclamacio_en_curs_pending_state'),
            ('som_account_invoice_pending', 'default_reclamacio_en_curs_pending_state'),
        ]

        ps_list = []
        for module, name in pending_states:
            ps_id = irmd_obj.get_object_reference( cursor, uid, module, name)[1]
            if ps_id:
                ps_list.append(ps_id)
        return ps_list


    def www_estat_pagament_ov(self, cursor, uid, inv_id):
        inv_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = inv_obj.browse(cursor, uid, inv_id)
        return self._www_estat_pagament_ov(cursor, uid, inv_data)

    def _www_estat_pagament_ov(self, cursor, uid, invoice):
        if invoice.state == 'open':
            if invoice.pending_state and \
               invoice.pending_state.id in self._pending_state_with_doing_by_id(cursor, uid):
                return _WWW_ESTAT_PAGAMENT[2]
            return _WWW_ESTAT_PAGAMENT[1]
        if invoice.state == 'paid':
            if invoice.group_move_id and \
               invoice.pending_state and \
               invoice.pending_state.id in self._pending_state_with_groupmove_by_id(cursor, uid):
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
            inv['estat_pagament'] = self._www_estat_pagament_ov(cursor, uid, inv_data)
            inv['enviat'] = inv_data.enviat
            inv['visible'] = inv_data.visible_ov
            result.append(inv)

        return result


GiscedataFacturacioFactura()
