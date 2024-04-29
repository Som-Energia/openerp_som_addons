# -*- coding: utf-8 -*-
import logging
from osv import osv, fields
from datetime import datetime, timedelta
from addons.giscedata_facturacio.giscedata_polissa import _get_polissa_from_invoice


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def _ff_consulta_pobresa_pendent(self, cr, uid, ids, name, args, context=None):
        logger = logging.getLogger(__name__)
        res = dict.fromkeys(ids, False)
        imd_obj = self.pool.get('ir.model.data')
        aips_obj = self.pool.get('account.invoice.pending.state')
        scp_obj = self.pool.get('som.consulta.pobresa')
        cfg_obj = self.pool.get('res.config')
        ndays = int(cfg_obj.get(cr, uid, 'nombre_dies_consulta_pobresa_vigent', '335'))

        try:
            consulta_state_id = imd_obj.get_object_reference(
                cr, uid, 'som_account_invoice_pending', 'pendent_consulta_probresa_pending_state',
            )[1]
        except ValueError as e:
            logger.warn(
                "pendent_consulta_probresa_pending_state is not ready "
                "(first installation), returning False as default\n", e.message
            )
            return res
        tall_state_id = imd_obj.get_object_reference(
            cr, uid, 'giscedata_facturacio_comer_bono_social', 'tall_pending_state',
        )[1]
        weight_consulta = aips_obj.browse(cr, uid, consulta_state_id).weight
        weight_tall = aips_obj.browse(cr, uid, tall_state_id).weight
        start_day_valid = (datetime.today() - timedelta(days=ndays)).strftime('%Y-%m-%d')

        for pol_id in res:
            pol = self.browse(cr, uid, pol_id)
            if pol.cups_np not in ["Barcelona", "Girona", "Lleida", "Tarragona"]:
                continue
            if not pol.pending_state:
                continue

            pol_state_id = aips_obj.search(cr, uid, [
                ('process_id', '=', pol.process_id.id),
                ('name', '=', pol.pending_state)])[0]
            weight_polissa_state = aips_obj.browse(cr, uid, pol_state_id).weight
            if weight_polissa_state < weight_consulta or weight_polissa_state > weight_tall:
                continue

            scp_list = scp_obj.search(cr, uid, [('polissa_id', '=', pol_id)])
            if not scp_list:  # No s'ha fet mai consulta pobresa
                res[pol_id] = True
                continue

            # Check consulta pobresa activa < 11 mesos data_tancament (closed) o obertura (pending)  # noqa: 501
            for scp_id in scp_list:
                scp = scp_obj.browse(cr, uid, scp_id)
                if (scp.state == 'done' and scp.date_closed < start_day_valid) or (
                        scp.state == 'pending' and scp.date < start_day_valid):
                    res[pol_id] = True
                    break

        return res

    def change_state(self, cursor, uid, ids, context):
        values = self.read(cursor, uid, ids, ['invoice_id'])
        return _get_polissa_from_invoice(
            self, cursor, uid, [value['invoice_id'][0] for value in values])

    _CHANGE_PENDING_STATE = {
        'giscedata.polissa': (lambda self, cr, uid, ids, c={}: ids, ['pending_state'], 20),
        'account.invoice': (_get_polissa_from_invoice, ['state', 'residual', 'pending_state'], 30),
        'account.invoice.pending.history': (change_state, ['change_date'], 10),
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
