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
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

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

    def check_conditions_lectures_calculades(self, cursor, uid, id, context):
        if isinstance(id, (tuple, list)):
            id = id[0]
        imd_o = self.pool.get('ir.model.data')
        cat_id = imd_o.get_object_reference(
            cursor, uid, 'som_facturacio_calculada', 'cat_gp_factura_calc'
        )[1]

        pol = self.browse(cursor, uid, id)
        if not pol.category_id or cat_id not in [x.id for x in pol.category_id]:
            return False, _(u"no té categoria")
        if pol.tarifa.name != '2.0TD':
            return False, _(u"no es 2.0TD")
        if pol.te_assignacio_gkwh:
            return False, _(u"té GenerationKWh")
        if pol.autoconsumo != '00':
            return False, _(u"té Autoconsum")
        if pol.facturacio_potencia == 'max': #!= 'icp'
            return False, _(u"té Maximetre")
        if pol.tg != '1':
            return False, _(u"no té telegestió")
        if pol.cnae.name != '9820':
            return False, _(u"no es un CNAE acceptat")
        gp_cat_o = self.pool.get('giscedata.polissa.category')
        gp_pobresa_id = gp_cat_o.search(cursor, uid, [('name', 'ilike', '%Pobresa Energ%')])
        if gp_pobresa_id and pol.category_id and gp_pobresa_id in [x.id for x in pol.category_id]:
            return False, _(u"té Pobresa Energètica")

        return True, _(u"ok")

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
            pol_name = self.read(cursor, uid, _id, ['name'], context)['name']
            crear_lectures, text = self.check_conditions_lectures_calculades(cursor, uid, _id, context=context)
            if not crear_lectures:
                msgs.append(u"La pòlissa {} no compleix les condicions per que {}".format(pol_name, text))
                continue
            pol_data = self.read(cursor, uid, _id, ['data_ultima_lectura','cups', 'data_ultima_lectura_f1', 'n_lect_calc'])
            data_ultima_lect = pol_data['data_ultima_lectura']
            data_ultima_lectura_f1 = pol_data['data_ultima_lectura_f1']

            if not data_ultima_lect:
                msgs.append(u"Pòlissa {} sense data ultima lectura".format(pol_name))
                continue
            if data_ultima_lect < data_ultima_lectura_f1:
                self.retrocedir_lot(cursor, uid, _id, context)
                self.write(cursor, uid, _id, {'n_lect_calc': 0})
                msgs.append(u"Pòlissa {} té lectura F1 amb data {} i data última factura {} i núm lectures calc successives = {}".format(
                    pol_name, data_ultima_lectura_f1, data_ultima_lect, pol_data['n_lect_calc']))
                continue
            if pol_data['n_lect_calc'] == 3:
                msgs.append(u"Pòlissa {} té 3 lectures calculades successives".format(pol_name))
                continue

            mtr_ids = mtr_o.search(cursor, uid, [
                ('polissa.id', '=', _id),
                ('active', '=', True)
            ])
            if not mtr_ids:
                msgs.append(u"No s'ha trobat comptador actiu per la pòlissa {}".format(pol_name))
                continue
            if len(mtr_ids) != 1:
                msgs.append(u"Multiples comptadors actius per la pòlissa {}".format(pol_name))
                continue
            mtr_id = mtr_ids[0]
            data_seguent_lect = (datetime.strptime(data_ultima_lect,'%Y-%m-%d') + timedelta(days=7)).strftime("%Y-%m-%d")
            start_date = (datetime.strptime(data_ultima_lect,'%Y-%m-%d') + timedelta(days=1)).strftime("%Y-%m-%d")
            cups_text = pol_data['cups'][1]
            tg_ids = tg_val_o.get_curve(cursor, uid, cups_text, data_ultima_lect, data_seguent_lect)
            if not tg_ids:
                msgs.append(u"Pòlissa {} amb data última {} sense corbes en la data {}".format(pol_name, data_ultima_lect, data_seguent_lect))
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
            self.write(cursor, uid, _id, {'n_lect_calc': pol_data['n_lect_calc'] + 1})
            msgs.append(u"Lectures creades en data {} per la polissa {}".format(data_seguent_lect, pol_name))
        self.retrocedir_lot(cursor, uid, ids, context=context)
        return msgs

    """
    @job(queue="facturacio_calculada")
    def crear_lectures_calculades_async(self, cursor, uid, ids, context=None):
        return _crear_lectures_calculades_sync(cursor, uid, pol_id, context=None)

    def _crear_lectures_calculades_sync(self, cursor, uid, pol_id, context=None):
    """

    _columns = {
        'n_lect_calc':fields.integer(string='Num lectures calculades consecutives',
            help="Número de lectures calculades a partir de CCH consecutives", readonly=True),
    }

    _defaults = {
        'n_lect_calc': lambda *a: 0,
    }

GiscedataPolissaCalculada()
