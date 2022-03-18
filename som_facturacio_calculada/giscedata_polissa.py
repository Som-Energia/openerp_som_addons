# -*- coding: utf-8 -*-
from osv import osv, fields
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools.translate import _
from oorq.decorators import job

class GiscedataPolissaCalculada(osv.osv):
    """
        Pòlissa per afegir les funcions per a la facturació calculada
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def retrocedir_lot(self, cursor, uid, ids, context=None):
        lot_o = self.pool.get('giscedata.facturacio.lot')

        last_lot_id = lot_o.search(cursor, uid, [
            ('state', '=', 'obert')
        ])[0]

        wiz_retrocedir_o = self.pool.get('wizard.move.contracts.prev.lot')
        ctx = {'incrementar_n_retrocedir': False}
        for _id in ids:

            lot_id = self.read(cursor, uid, _id, ['lot_facturacio'], context)['lot_facturacio'][0]
            if lot_id > last_lot_id:
                wiz_id = wiz_retrocedir_o.create(cursor, uid, {}, context=context)
                wiz_retrocedir_o.move_one_contract_to_prev_lot(cursor, uid, [wiz_id], _id, context=ctx)

    def crear_lectures_calculades(self, cursor, uid, ids, context=None):
        imd_o = self.pool.get('ir.model.data')
        mtr_o = self.pool.get('giscedata.lectures.comptador')
        tg_val_o = self.pool.get('tg.cchval')

        wiz_measures_curve_o = self.pool.get('wizard.measures.from.curve')
        lc_origin = imd_o.get_object_reference(
            cursor, uid, 'som_facturacio_calculada', 'origen_lect_calculada'
        )[1]
        msgs = []
        for _id in ids:
            mtr_ids = mtr_o.search(cursor, uid, [
                ('polissa.id', '=', _id),
                ('active', '=', True)
            ])
            if not mtr_ids:
                msgs.append("No s'ha trobat comptador actiu per la pòlissa ID: {}".format(_id))
                continue
            if len(mtr_ids) != 1:
                msgs.append("Multiples comptadors actius per la pòlissa ID: {}".format(_id))
                continue
            mtr_id = mtr_ids[0]

            pol_data = self.read(cursor, uid, _id, ['data_ultima_lectura','cups'])
            data_ultima_lect = pol_data['data_ultima_lectura']

            if not data_ultima_lect:
                msgs.append("Pòlissa ID sense data ultima lectura: {}".format(_id))
                continue
            data_seguent_lect = (datetime.strptime(data_ultima_lect,'%Y-%m-%d') + timedelta(days=7)).strftime("%Y-%m-%d")
            start_date = (datetime.strptime(data_ultima_lect,'%Y-%m-%d') + timedelta(days=1)).strftime("%Y-%m-%d")
            cups_text = pol_data['cups'][1]
            tg_ids = tg_val_o.search(cursor, uid, [
                ('name', '=', cups_text),
                ('datetime', '>', data_seguent_lect),
            ], limit=1)
            if not tg_ids:
                msgs.append("Pòlissa ID amb data última {} sense corbes en la data {}: {}".format(data_ultima_lect, data_seguent_lect, _id))
                continue
            vals = {
                'measure_origin': lc_origin,
                'insert_reactive': False,
                'insert_maximeters': False,
                'measure_date': data_seguent_lect,
                'start_date': start_date,
                'meter_id': mtr_id,
            }
            ctx = {
                'from_model': 'giscedata.lectures.comptador',
                'active_ids': [mtr_id], 'active_id': mtr_id
            }
            wiz_id = wiz_measures_curve_o.create(cursor, uid, vals, context=ctx)

            wiz_measures_curve_o.load_measures(cursor, uid, [wiz_id], context=ctx)
            wiz_measures_curve_o.create_measures(cursor, uid, [wiz_id], context=ctx)
            msgs.append("Lectures creades en data {} per la polissa {}".format(data_seguent_lect, _id))
        self.retrocedir_lot(cursor, uid, ids, context=context)
        return msgs

    """
    @job(queue="facturacio_calculada")
    def crear_lectures_calculades_async(self, cursor, uid, ids, context=None):
        return _crear_lectures_calculades_sync(cursor, uid, pol_id, context=None)

    def _crear_lectures_calculades_sync(self, cursor, uid, pol_id, context=None):
    """

    _columns = {

    }
    _defaults = {
    }

GiscedataPolissaCalculada()