# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta
from giscedata_facturacio.report.utils import get_atr_price
from dateutil.relativedelta import relativedelta


class WizardContractPowerOptimization(osv.osv_memory):
    _name = "wizard.contract.power.optimization"

    def _date_lecture_in_range(self, cursor, uid, value_date, context=None):
        if context is None:
            context = {}

        result = False
        wizard = self.browse(cursor, uid, wiz_id, context=context)

        start_date = datetime.strptime(wiz.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(wiz.end_date, '%Y-%m-%d')
        datetimed_date = datetime.strptime(value_date, '%Y-%m-%d')

        if datetimed_date >= start_date and datetimed_date < end_date:
            result = True
        return result

    def get_maximeters_power(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        wizard = self.browse(cursor, uid, wiz_id, context=context)

        # Primer hem de mirar quins comptadors hem de mirar
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)

        start_date = wiz.start_date
        end_date = wiz.end_date

        comptadors = []
        maximetres = {}

        comptadors = pol_obj.comptadors_actius(pol_id, start_date, end_date)

        for comptador in comptadors:
            for lectura in comptador.lectures_pot:
                lectura_date = comptador.name
                if _date_lecture_in_range(cursor, uid, lectura_date, context=context):
                    month_lectura_date = datetime.strftime(lectura_date, '%m%Y')
                    period = lectura.periode.name
                    if not maximeter.get(month_lectura_date):
                        maximetres[month_lectura_date] = {}
                    if not maximeter[month_lectura_date].get(period):
                        maximetres[month_lectura_date][period] = 0
                    if maximetres[month_lectura_date][period] < lectura.lectura:
                        maximetres[month_lectura_date][period] = lectura.lectura

        return maximetres

    def get_periods_power(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        wizard = self.browse(cursor, uid, wiz_id, context=context)

        wiz.potencia_p1 = polissa.potencies_periode[0].potencia
        wiz.potencia_p2 = polissa.potencies_periode[1].potencia
        wiz.potencia_p3 = polissa.potencies_periode[2].potencia
        wiz.potencia_p4 = polissa.potencies_periode[3].potencia
        wiz.potencia_p5 = polissa.potencies_periode[4].potencia
        wiz.potencia_p6 = polissa.potencies_periode[5].potencia

    def get_periods_power_price(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        wizard = self.browse(cursor, uid, wiz_id, context=context)

        wiz.preu_potencia_p1 = get_atr_price(
            cursor, uid, polissa_id, 'P1', 'tp', context=context
        )
        wiz.preu_potencia_p2 = get_atr_price(
            cursor, uid, polissa_id, 'P2', 'tp', context=context
        )
        wiz.preu_potencia_p3 = get_atr_price(
            cursor, uid, polissa_id, 'P3', 'tp', context=context
        )
        wiz.preu_potencia_p4 = get_atr_price(
            cursor, uid, polissa_id, 'P4', 'tp', context=context
        )
        wiz.preu_potencia_p5 = get_atr_price(
            cursor, uid, polissa_id, 'P5', 'tp', context=context
        )
        wiz.preu_potencia_p6 = get_atr_price(
            cursor, uid, polissa_id, 'P6', 'tp', context=context
        )

    def get_excess_price(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        wizard = self.browse(cursor, uid, wiz_id, context=context)

        wiz.preu_exces = get_atr_price(
            cursor, uid, polissa_id, 'P1', 'epm', context=context
        )

    def get_optimization_required_data(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        # We fill the wizard data
        self.get_periods_power(cursor, uid, wiz_id, polissa_id, context=context)
        self.get_periods_power_price(cursor, uid, wiz_id, polissa_id, context=context)
        self.get_excess_price(cursor, uid, wiz_id, polissa_id, context=context)

    def pass_maximeter_validation(self, cursor, uid, ids, context=None):
        pass

    def execute_optimization_script(self, cursor, uid, ids, context=None):
        pass

    def get_optimization(self, cursor, uid, ids, context=None):
        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get("active_ids")
        wizard = self.browse(cursor, uid, ids[0])

        for polissa_id in active_ids:
            self.get_optimization_required_data(
                cursor, uid, wiz_id, polissa_id, context=context
            )

        return {"type": "ir.actions.act_window_close"}

    def _default_state(self, cursor, uid, context=None):
        if not context:
            context = {}
        state = 'one'
        if context.get('active_ids'):
            if len(context.get('active_ids')) > 1:
                state = 'multiple'
        return state

    def _compute_end_date(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        for wiz in self.browse(cr, uid, ids, context):
            end_date = wiz.start_date + relativedelta(years=+1)
            result[wiz.id] = end_ate
        return result

    def _default_start_date(self, cursor, uid, context=None):
        if not context:
            context = {}

        last_year = (datetime.now() - timedelta(year=1)).year
        start_date = '{}-01-01'.format(last_year)
        return start_date

    _columns = {
        'state': fields.selection(
            [
                ('one', 'Un'),
                ('multiple', 'Varis'),
                ('result', 'Resultat')
            ],
        'State'),

        'preu_exces': fields.float('Preu excés maxímetre'),

        'start_date': fields.datetime('Data d\'inici'),
        'end_date': fields.function(_compute_end_date, method=True, string='Data final', type='date'),

        'potencia_p1': fields.integer('Potència P1'),
        'potencia_p2': fields.integer('Potència P2'),
        'potencia_p3': fields.integer('Potència P3'),
        'potenica_p4': fields.integer('Potència P4'),
        'potencia_p5': fields.integer('Potència P5'),
        'potencia_p6': fields.integer('Potència P6'),

        'preu_potencia_p1': fields.float('Preu potència P1', digits=(16, 6)),
        'preu_potencia_p2': fields.float('Preu potència P2', digits=(16, 6)),
        'preu_potencia_p3': fields.float('Preu potència P3', digits=(16, 6)),
        'preu_potenica_p4': fields.float('Preu potència P4', digits=(16, 6)),
        'preu_potencia_p5': fields.float('Preu potència P5', digits=(16, 6)),
        'preu_potencia_p6': fields.float('Preu potència P6', digits=(16, 6)),

        'potencies_maximetres': fileds.text('Potències dels maxímetres')
    }

    _defaults = {
        'state': _default_state,
        'start_date': _default_start_date
    }


WizardCanviarContrasenya()
