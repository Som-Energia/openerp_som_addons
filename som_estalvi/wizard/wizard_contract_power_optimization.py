# -*- coding: utf-8 -*-
import os, subprocess
from StringIO import StringIO
from osv import osv, fields
from datetime import datetime, timedelta
from giscedata_facturacio.report.utils import get_atr_price
from dateutil.relativedelta import relativedelta
import base64
import csv
import json

HEADER = [
    'nEstimates', 'current_cost', 'total_cost', 'optimal_powers_P1', 'optimal_powers_P2', 'optimal_powers_P3',
    'optimal_powers_P4', 'optimal_powers_P5', 'optimal_powers_P6', 'total_maximeters_P1',
    'total_maximeters_P2', 'total_maximeters_P3', 'total_maximeters_P4', 'total_maximeters_P5',
    'total_maximeters_P6', 'total_powers_P1', 'total_powers_P2', 'total_powers_P3',
    'total_powers_P4', 'total_powers_P5', 'total_powers_P6'
]

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

    def _calculate_maximeter_excess_price(self, cursor, uid, wiz_id, month, maximeter_power, period_power, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, wiz_id, context=context)

        month_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        maximeter_excess_price = 0

        maximeter_excess = maximeter_power - period_power
        if maximeter_excess > 0:
            maximeter_excess_price = 2 * maximeter_excess * wiz.excess_price * month_days[month-1]

        return maximeter_excess_price

    def _calculate_current_cost(self, cursor, uid, wiz_id, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, wiz_id, context=context)

        contracted_power_price = 0

        contracted_power_price += wiz.power_p1 * wiz.power_price_p1
        contracted_power_price += wiz.power_p2 * wiz.power_price_p2
        contracted_power_price += wiz.power_p3 * wiz.power_price_p3
        contracted_power_price += wiz.power_p4 * wiz.power_price_p4
        contracted_power_price += wiz.power_p5 * wiz.power_price_p5
        contracted_power_price += wiz.power_p6 * wiz.power_price_p6

        total_maximeter_price = 0

        maximeters_powers = json.loads(wiz.maximeters_powers)
        for date in maximeters_powers:
            month = datetime.strptime(date, '%m%Y').month
            for period in maximeters_powers[date]:
                maximeter_period_month = maximeters_powers[date][period]
                if period == 'P1':
                    total_maximeter_price += self._calculate_maximeter_excess_price(
                        cursor, uid, wiz_id, month, maximeter_period_month, wiz.power_p1, context=context
                    )
                elif period == 'P2':
                    total_maximeter_price += self._calculate_maximeter_excess_price(
                        cursor, uid, wiz_id, month, maximeter_period_month, wiz.power_p2, context=context
                    )
                elif period == 'P3':
                    total_maximeter_price += self._calculate_maximeter_excess_price(
                        cursor, uid, wiz_id, month, maximeter_period_month, wiz.power_p3, context=context
                    )
                elif period == 'P4':
                    total_maximeter_price += self._calculate_maximeter_excess_price(
                        cursor, uid, wiz_id, month, maximeter_period_month, wiz.power_p4, context=context
                    )
                elif period == 'P5':
                    total_maximeter_price += self._calculate_maximeter_excess_price(
                        cursor, uid, wiz_id, month, maximeter_period_month, wiz.power_p5, context=context
                    )
                elif period == 'P6':
                    total_maximeter_price += self._calculate_maximeter_excess_price(
                        cursor, uid, wiz_id, month, maximeter_period_month, wiz.power_p6, context=context
                    )

            result = total_maximeter_price + contracted_power_price
            wiz.write({'current_cost' : result}, context=context)

    def _calculate_number_of_estimates(self, cursor, uid, wiz_id, maximeters_float, context=None):
        if context is None:
            context = {}
        wiz = self.browse(cursor, uid, wiz_id, context=context)
        #per cada mes, cada periode diferent de 0 ha de ser pX*0.85

        nEstimates=0
        for month in maximeters_float:
            if (maximeters_float[month]['P1'] == 0 or maximeters_float[month]['P1'] == (wiz.power_p1 * 0.85)) and \
            (maximeters_float[month]['P2'] == 0 or maximeters_float[month]['P2'] == (wiz.power_p2 * 0.85)) and \
            (maximeters_float[month]['P3'] == 0 or maximeters_float[month]['P3'] == (wiz.power_p3 * 0.85)) and \
            (maximeters_float[month]['P4'] == 0 or maximeters_float[month]['P4'] == (wiz.power_p4 * 0.85)) and \
            (maximeters_float[month]['P5'] == 0 or maximeters_float[month]['P5'] == (wiz.power_p5 * 0.85)) and \
            (maximeters_float[month]['P6'] == 0 or maximeters_float[month]['P6'] == (wiz.power_p6 * 0.85)):
                nEstimates+=1

        wiz.write({'nEstimates' : nEstimates}, context=context)

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
        return output[:-2][1:]

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
        maximeters = {}
        maximeters_float = {}

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
                        maximeters[month_lectura_date] = {}
                        maximeters_float[month_lectura_date] = {}
                    if not maximeters[month_lectura_date].get(period):
                        maximeters[month_lectura_date][period] = 0
                        maximeters_float[month_lectura_date][period] = 0
                    if maximeters[month_lectura_date][period] < lectura.lectura:
                        maximeters[month_lectura_date][period] = int(round(lectura.lectura))
                        maximeters_float[month_lectura_date][period] = lectura.lectura

        vals = {'maximeters_powers': json.dumps(maximeters, sort_keys=True, indent=4)}
        wiz.write(vals, context=context)

        self._calculate_number_of_estimates(cursor, uid, wiz_id, maximeters_float, context=context)
        self._calculate_current_cost(cursor, uid, wiz_id, context=context)

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
            "float_p6": polissa.potencies_periode[5].potencia,
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
            )[0],
            "power_price_p2": get_atr_price(
                cursor, uid, polissa, 'P2', 'tp', context=context, with_taxes=True
            )[0],
            "power_price_p3": get_atr_price(
                cursor, uid, polissa, 'P3', 'tp', context=context, with_taxes=True
            )[0],
            "power_price_p4": get_atr_price(
                cursor, uid, polissa, 'P4', 'tp', context=context, with_taxes=True
            )[0],
            "power_price_p5": get_atr_price(
                cursor, uid, polissa, 'P5', 'tp', context=context, with_taxes=True
            )[0],
            "power_price_p6": get_atr_price(
                cursor, uid, polissa, 'P6', 'tp', context=context, with_taxes=True
            )[0],
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
        )[0]
        wiz.write({'excess_price': excess_price}, context=context)

    def button_get_optimization_required_data(self, cursor, uid, wiz_id, context=None):
        if context is None:
            context = {}

        if len(context['active_ids']) == 1:
            self.get_optimization_required_data(cursor, uid, wiz_id[0], context['active_ids'][0], context=context)
        else:
            raise  osv.except_osv(_('Error !'), _('Aquest boto només funciona per una polissa'))

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

        values = self.browse(cursor, uid, wiz_id, context=context)
        data = {
            'power_price': [],
            'excess_price': values['excess_price'],
            'maximeters_powers': [],
            'contract61': False,
            'power_p6': int(values['power_p6']),
        }

        for k,v in sorted(values.read()[0].items()):
            if 'power_price' in k:
                data['power_price'].append(v)
            elif 'maximeters_powers' in k:
                maximeters_powers = json.loads(values[k])
                for mes in sorted(maximeters_powers):
                    for periode in sorted(maximeters_powers[mes]):
                        data['maximeters_powers'] += [maximeters_powers[mes][periode]]

        mzn_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../scripts/optimization.mzn")
        data['mzn_path'] = mzn_path
        json_data = json.dumps(data)
        return json_data

    def button_execute_optimization_script(self, cursor, uid, wiz_id, context=None):
        if context is None:
            context = {}

        if len(context['active_ids']) == 1:
            optimization = self.execute_optimization_script(
                cursor, uid, wiz_id[0], context['active_ids'][0], context=context
            )
            self.generate_optimization_as_csv(
                cursor, uid, wiz_id[0], [optimization], context=context
            )
            wiz = self.browse(cursor, uid, wiz_id[0], context=context)
            wiz.write({'state': 'result'}, context=context)
        else:
            raise  osv.except_osv(_('Error !'), _('Aquest boto només funciona per una polissa'))

    def beautify_output(self, cursor, uid, wiz_id, output, context=None):
        if context is None:
            context = {}

        result = {}
        optimization = json.loads(output)
        wiz = self.browse(cursor, uid, wiz_id, context=context)

        i = 1
        for val in optimization['optimalPowers']:
            if i != 6:
                result['optimal_powers_P{}'.format(i)] = val
            elif i == 6:
                if val == wiz.power_p6:
                    result['optimal_powers_P{}'.format(i)] = wiz.float_p6
                else:
                    result['optimal_powers_P{}'.format(i)] = val
            i += 1
        i = 1
        for val in optimization['totalMaximeters']:
            result['total_maximeters_P{}'.format(i)] = val
            i += 1
        i = 1
        for val in optimization['totalPowers']:
            result['total_powers_P{}'.format(i)] = val
            i += 1

        result['total_cost'] = optimization['totalCost']
        result['nEstimates'] = wiz.nEstimates
        result['current_cost'] = wiz.current_cost

        return result

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

        output = self.check_output(data, command)
        result = self.beautify_output(cursor, uid, wiz_id, output, context=context)
        return result

    def get_optimization(self, cursor, uid, ids, context=None):
        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get("active_ids")
        wiz = self.browse(cursor, uid, ids[0])

        optimizations = []

        for polissa_id in active_ids:
            self.get_optimization_required_data(
                cursor, uid, wiz.id, polissa_id, context=context
            )
            polissa_optimization = self.execute_optimization_script(
                cursor, uid, wiz.id, polissa_id, context=context
            )
            optimizations.append(polissa_optimization)

        self.generate_optimization_as_csv(
            cursor, uid, wiz.id, optimizations, context=context
        )
        wiz.write({'state': 'result'})

    def generate_optimization_as_csv(self, cursor, uid, wiz_id, optimizations, context=None):
        if context is None:
            context = {}

        wizard = self.browse(cursor, uid, wiz_id, context=context)

        csv_file = StringIO()
        writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(HEADER)
        for optimization in optimizations:
            row = []
            for value in HEADER:
                row.append(optimization[value])
            writer.writerow(row)

        res_file = csv_file.getvalue()

        #TODO
        # Quan costa l'any actual i l'estalvi

        wizard.write({'report': base64.b64encode(res_file), 'filename_report': "_optim"+".csv"})

    def _default_state(self, cursor, uid, context=None):
        if not context:
            context = {}
        state = 'one'
        if context.get('active_ids'):
            if len(context.get('active_ids')) > 1:
                state = 'multiple'
        return state

    def _compute_end_date(self, cursor, uid, ids, field_name, arg, context={}):
        result = {}
        for wiz in self.browse(cr, uid, ids, context):
            end_date = datetime.strptime(wiz.start_date, '%Y-%m-%d') + relativedelta(years=+1)
            result[wiz.id] = datetime.strftime(end_date,'%Y-%m-%d')
        return result

    def onchange_start_date(self, cursor, uid, ids, start_date, context={}):
        res = {'value': {}, 'domain': {}, 'warning': {}}

        if start_date:
            year_end_date = (datetime.strptime(start_date, '%Y-%m-%d') + relativedelta(years=+1)).year
            end_date = '{}-01-01'.format(year_end_date)
            res['value'].update({'end_date': end_date})
        return res

    def _default_start_date(self, cursor, uid, context=None):
        if not context:
            context = {}

        last_year = (datetime.now() - relativedelta(years=+1)).year
        start_date = '{}-01-01'.format(last_year)
        return start_date

    def _default_end_date(self, cursor, uid, context=None):
        if not context:
            context = {}

        last_year = datetime.now().year
        end_date = '{}-01-01'.format(last_year)
        return end_date

    _columns = {
        'state': fields.selection(
            [
                ('one', 'Un'),
                ('multiple', 'Varis'),
                ('result', 'Resultat')
            ],
        'State'),

        'excess_price': fields.float('Preu excés maxímetre'),

        'start_date': fields.date('Data inici'),
        'end_date': fields.date('Data final'),
        'nEstimates': fields.integer('Nombre de mesos amb maximetres estimats'),
        'current_cost': fields.integer('Cost actual'),

        'power_p1': fields.integer('Potència P1'),
        'power_p2': fields.integer('Potència P2'),
        'power_p3': fields.integer('Potència P3'),
        'power_p4': fields.integer('Potència P4'),
        'power_p5': fields.integer('Potència P5'),
        'power_p6': fields.integer('Potència P6'),
        'float_p6': fields.float('Potència amb decimals P6'),

        'power_price_p1': fields.float('Preu potència P1', digits=(16, 6)),
        'power_price_p2': fields.float('Preu potència P2', digits=(16, 6)),
        'power_price_p3': fields.float('Preu potència P3', digits=(16, 6)),
        'power_price_p4': fields.float('Preu potència P4', digits=(16, 6)),
        'power_price_p5': fields.float('Preu potència P5', digits=(16, 6)),
        'power_price_p6': fields.float('Preu potència P6', digits=(16, 6)),

        'maximeters_powers': fields.text('Potències dels maxímetres'),

        'report': fields.binary('Resultat'),
        'filename_report': fields.char('Nom fitxer exportat', size=256),
    }

    _defaults = {
        'state': _default_state,
        'start_date': _default_start_date,
        'end_date': _default_end_date
    }


WizardContractPowerOptimization()
