# -*- coding: utf-8 -*-
import os, subprocess
from osv import osv, fields
from datetime import datetime, timedelta
from giscedata_facturacio.report.utils import get_atr_price
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import json


class WizardContractPowerOptimization(osv.osv_memory):
    _name = "wizard.contract.power.optimization"

    def _date_lecture_in_range(self, cursor, uid, wiz_id, value_date, context=None):
        if context is None:
            context = {}

        result = False
        wiz = self.browse(cursor, uid, wiz_id, context=context)

        start_date = datetime.strptime(wiz.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(wiz.end_date, '%Y-%m-%d')
        datetimed_date = datetime.strptime(value_date, '%Y-%m-%d')

        if datetimed_date >= start_date and datetimed_date < end_date:
            result = True
        return result

    def check_output(self, data, *popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, *popenargs, **kwargs)
        output = process.communicate(input=data)[0]
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output

    def get_maximeters_power(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        comptador_obj = self.pool.get('giscedata.lectures.comptador')
        wiz = self.browse(cursor, uid, wiz_id, context=context)

        # Primer hem de mirar quins comptadors hem de mirar
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)

        start_date = wiz.start_date
        end_date = wiz.end_date

        comptadors = []
        maximeters = OrderedDict()

        comptadors_ids = pol_obj.comptadors_actius(cursor, uid, polissa_id, start_date, end_date)
        comptadors = comptador_obj.browse(cursor, uid, comptadors_ids, context=context)

        for comptador in comptadors:
            for lectura in comptador.lectures_pot:
                lectura_date = lectura.name
                if self._date_lecture_in_range(cursor, uid, wiz_id, lectura_date, context=context):
                    lectura_date_dated = datetime.strptime(lectura_date, '%Y-%m-%d')
                    month_lectura_date = datetime.strftime(lectura_date_dated, '%m%Y')
                    period = lectura.periode.name
                    if not maximeters.get(month_lectura_date):
                        maximeters[month_lectura_date] = OrderedDict()
                    if not maximeters[month_lectura_date].get(period):
                        maximeters[month_lectura_date][period] = 0
                    if maximeters[month_lectura_date][period] < lectura.lectura:
                        maximeters[month_lectura_date][period] = int(round(lectura.lectura))

        vals = {'maximeters_powers': maximeters}
        wiz.write(vals, context=context)

    def get_periods_power(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        wiz = self.browse(cursor, uid, wiz_id, context=context)

        # De moment ho optimitzarem amb ints. TODO preguntar a EiE
        vals = {
            "power_p1": round(polissa.potencies_periode[0].potencia),
            "power_p2": round(polissa.potencies_periode[1].potencia),
            "power_p3": round(polissa.potencies_periode[2].potencia),
            "power_p4": round(polissa.potencies_periode[3].potencia),
            "power_p5": round(polissa.potencies_periode[4].potencia),
            "power_p6": round(polissa.potencies_periode[5].potencia),
        }
        wiz.write(vals, context=context)

    def get_periods_power_price(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        context['date'] = datetime.today().strftime("%Y-%m-%d")
        context['potencia_anual'] = True
        context['sense_agrupar'] = True

        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        wiz = self.browse(cursor, uid, wiz_id, context=context)

        vals = {
            "power_price_p1": get_atr_price(
                cursor, uid, polissa, 'P1', 'tp', context=context, with_taxes=True
            ),
            "power_price_p2": get_atr_price(
                cursor, uid, polissa, 'P2', 'tp', context=context, with_taxes=True
            ),
            "power_price_p3": get_atr_price(
                cursor, uid, polissa, 'P3', 'tp', context=context, with_taxes=True
            ),
            "power_price_p4": get_atr_price(
                cursor, uid, polissa, 'P4', 'tp', context=context, with_taxes=True
            ),
            "power_price_p5": get_atr_price(
                cursor, uid, polissa, 'P5', 'tp', context=context, with_taxes=True
            ),
            "power_price_p6": get_atr_price(
                cursor, uid, polissa, 'P6', 'tp', context=context, with_taxes=True
            ),
        }
        wiz.write(vals, context=context)

    def get_excess_price(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        context['date'] = datetime.today().strftime("%Y-%m-%d")
        context['potencia_anual'] = True
        context['sense_agrupar'] = True

        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        wiz = self.browse(cursor, uid, wiz_id, context=context)

        excess_price = get_atr_price(
            cursor, uid, polissa, 'P1', 'epm', context=context, with_taxes=True
        )
        wiz.write({'excess_price': excess_price}, context=context)

    def get_optimization_required_data(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        # We fill the wizard data
        self.get_periods_power(cursor, uid, wiz_id, polissa_id, context=context)
        preuPotencies = self.get_periods_power_price(cursor, uid, wiz_id, polissa_id, context=context)
        preuPenalitzacio = self.get_excess_price(cursor, uid, wiz_id, polissa_id, context=context)
        potenciaMax = self.get_maximeters_power(cursor, uid, wiz_id, polissa_id, context=context)

    def pass_maximeter_validation(self, cursor, uid, ids, context=None):
        pass

    def serializate_wizard_data(self, cursor, uid, wiz_id, context=None):
        if context is None:
            context = {}
        values = self.browse(cursor, uid, wiz_id, context=context).read()[0]
        data = {
            'power_price': [],
            'excess_price': values['excess_price'][0],
            'maximeters_powers': [],
            'contract61': False,
            'power_p6': int(values['power_p6']),
        }

        for k,v in sorted(values.items()):
            if 'power_price' in k:
                data['power_price'].append(v[0])
            elif 'maximeters_powers' in k:
                for mes in sorted(values[k]):
                    for periode in sorted(values[k][mes]):
                        data['maximeters_powers'] += [values[k][mes][periode]]

        mzn_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../scripts/optimization.mzn")
        data['mzn_path'] = mzn_path
        json_data = json.dumps(data)
        return json_data

    def execute_optimization_script(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}

        cfg_obj = self.pool.get("res.config")

        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../scripts/optimization.py")
        mzn_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../scripts/optimization.mzn")
        data = self.serializate_wizard_data(cursor, uid, wiz_id, context=context)

        virtualenv = cfg_obj.get(
            cursor, uid,
            "som_crawlers_massive_importer_python_path",
            "/home/erp/.virtualenvs/massive/bin/python",
        )

        if not os.path.exists(virtualenv):
            raise Exception("Not virtualenv of massive importer found")

        command = ['{} {}'.format(virtualenv, script_path)]

        result = self.check_output(data, command)
        return result

    def get_optimization(self, cursor, uid, ids, context=None):
        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get("active_ids")
        wiz = self.browse(cursor, uid, ids[0])

        for polissa_id in active_ids:
            self.get_optimization_required_data(
                cursor, uid, wiz_id, polissa_id, context=context
            )
            self.execute_optimization_script(
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
            end_date = datetime.strptime(wiz.start_date, '%Y-%m-%d') + relativedelta(years=+1)
            result[wiz.id] = datetime.strftime(end_date,'%Y-%m-%d')
        return result

    def _default_start_date(self, cursor, uid, context=None):
        if not context:
            context = {}

        last_year = (datetime.now() - relativedelta(years=+1)).year
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

        'excess_price': fields.float('Preu excés maxímetre'),

        'start_date': fields.datetime('Data d\'inici'),
        'end_date': fields.function(_compute_end_date, method=True, string='Data final', type='date'),

        'power_p1': fields.integer('Potència P1'),
        'power_p2': fields.integer('Potència P2'),
        'power_p3': fields.integer('Potència P3'),
        'power_p4': fields.integer('Potència P4'),
        'power_p5': fields.integer('Potència P5'),
        'power_p6': fields.integer('Potència P6'),

        'power_price_p1': fields.float('Preu potència P1', digits=(16, 6)),
        'power_price_p2': fields.float('Preu potència P2', digits=(16, 6)),
        'power_price_p3': fields.float('Preu potència P3', digits=(16, 6)),
        'power_price_p4': fields.float('Preu potència P4', digits=(16, 6)),
        'power_price_p5': fields.float('Preu potència P5', digits=(16, 6)),
        'power_price_p6': fields.float('Preu potència P6', digits=(16, 6)),

        'maximeters_powers': fields.text('Potències dels maxímetres')
    }

    _defaults = {
        'state': _default_state,
        'start_date': _default_start_date
    }


WizardContractPowerOptimization()
