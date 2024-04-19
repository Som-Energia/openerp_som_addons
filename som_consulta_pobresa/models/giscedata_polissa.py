# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta

DIES_VIGENCIA_CONSULTA = 335


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def _ff_consulta_pobresa_pendent(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0)
        imd_obj = self.pool.get('ir.model.data')
        aips_obj = self.pool.get('account.invoice.pending.state')
        scp_obj = self.pool.get('som.consulta.pobresa')

        consulta_state_id = imd_obj.get_object_reference(
            cr, uid, 'som_account_invoice_pending', 'pendent_consulta_probresa_pending_state',
        )
        tall_state_id = imd_obj.get_object_reference(
            cr, uid, 'giscedata_facturacio_comer_bono_social', 'tall_pending_state',
        )
        weight_consulta = aips_obj.browse(cr, uid, consulta_state_id).weight
        weight_tall = aips_obj.browse(cr, uid, tall_state_id).weight
        start_day_valid = (datetime.today()
                           - timedelta(days=DIES_VIGENCIA_CONSULTA)).strftime('%Y-%m-%d')

        for pol_id in res:
            res[pol_id] = False
            pol = self.browse(cr, uid, pol_id)
            if not pol.pending_state:
                continue

            pol_state_id = aips_obj.search(cr, uid, [
                ('process_id', '=', pol.process_id.id),
                ('name', '=', pol.pending_state)])[0]
            weight_polissa_state = aips_obj.browse(cr, uid, pol_state_id).weight
            if weight_polissa_state < weight_consulta or weight_polissa_state > weight_tall:
                continue

            # Check consulta pobresa activa < 11 mesos data_tancament (closed) o obertura (pending)  # noqa: 501
            scp_list = scp_obj.search(cr, uid, [('polissa_id', '=', pol_id)])
            for scp_id in scp_list:
                scp = scp_obj.browse(cr, uid, scp_id)
                if (scp.state == 'done' and scp.date_closed > start_day_valid) or (
                        scp.state == 'pending' and scp.date > start_day_valid):
                    res[pol_id] = True
                    break

        return res

    _CHANGE_PENDING_STATE = {
        'giscedata.polissa': (lambda self, cr, uid, ids, c={}: ids, ['pending_state'], 20),
    }

    _columns = {
        'consulta_pobresa_pendent': fields.function(
            _ff_consulta_pobresa_pendent,
            method=True,
            type='boolean',
            string='Consulta pobresa pendent',
            store=_CHANGE_PENDING_STATE
        ),
    }


GiscedataPolissa()
