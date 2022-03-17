# -*- coding: utf-8 -*-
from osv import osv, fields
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools.translate import _

class GiscedataPolissaInfoenergia(osv.osv):
    """
        Pòlissa per afegir els camps relacionats amb infoenergia
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def retrocedir_lot(self, cursor, uid, ids, context=context):
        #TODO: check if necessary retrocedir
        wiz_retrocedir_o = self.pool.get('wizard.move.contracts.prev.lot')
        ctx = {'incrementar_n_retrocedir': False}
        for _id in ids:
            wiz_id = wiz_retrocedir_o.create(cursor, uid, {}, context=context)
            wiz_retrocedir_o.move_one_contract_to_prev_lot(cursor, uid, [wiz_id], _id, context=ctx):

    def crear_lectures_calculades(self, cursor, uid, ids, context=context):
        imd_o = self.pool.get('ir.model.data')
        wiz_measures_curve_o = self.pool.get('wizard.measures.from.curve')
        lc_origin = imd_o.get_object_reference(
            cursor, uid, 'som_facturacio_calculada', 'origen_lect_calculada'
        )[1]
        for _id in ids:
            meter_id = #TODO
            vals = {
                'measure_origin': lc_origin,
                'insert_reactive': False,
                'insert_maximeters': False,
                'measure_date': #TODO:
            }
            ctx = {
                'from_model': 'giscedata.lectures.comptador',
                'active_ids': [meter_id], 'active_id': meter_id
            }
            wiz_id = wiz_measures_curve_o.create(cursor, uid, vals, context=ctx)
            wiz_measures_curve_o.load_measures(cursor, uid, [wiz_id], context=ctx)
            wiz_measures_curve_o.create_measures(cursor, uid, [wiz_id], context=ctx)

        self.retrocedir_lot(cursor, uid, ids, context=context)

    _columns = {

    }
    _defaults = {
    }

GiscedataPolissaInfoenergia()