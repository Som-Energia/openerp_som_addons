# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta
from giscedata_facturacio.report.utils import get_atr_price


class WizardContractPowerOptimization(osv.osv_memory):
    _name = "wizard.contract.power.optimization"

    def get_optimization_required_data(self, cursor, uid, wiz_id, polissa_id, context=None):
        if context is None:
            context = {}
        if not context.get('date'):
            last_year = (datetime.now() - timedelta(year=1)).year
            context['date'] = '{}-01-01'.format(last_year)

        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)

        wizard = self.browse(cursor, uid, wiz_id, context=context)

        wiz.potencia_p1 = polissa.potencies_periode[0].potencia
        wiz.potencia_p2 = polissa.potencies_periode[1].potencia
        wiz.potencia_p3 = polissa.potencies_periode[2].potencia
        wiz.potencia_p4 = polissa.potencies_periode[3].potencia
        wiz.potencia_p5 = polissa.potencies_periode[4].potencia
        wiz.potencia_p6 = polissa.potencies_periode[5].potencia

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

        wiz.preu_exces = get_atr_price(
            cursor, uid, polissa_id, 'P1', 'epm', context=context
        )

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

    _columns = {
        'state': fields.selection(
            [
                ('one', 'Un'),
                ('multiple', 'Varis'),
                ('result', 'Resultat')
            ],
        'State'),

        'preu_exces': fields.float('Preu excés maxímetre'),

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
        'state': _default_state
    }


WizardCanviarContrasenya()
