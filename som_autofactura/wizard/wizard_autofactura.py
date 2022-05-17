# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class WizardAutofactura(osv.osv_memory):
    _name = 'wizard.autofactura'

    def do(self, cursor, uid, ids, context=None):
        task_obj = self.pool.get('som.autofactura.task')
        imd_obj = self.pool.get('ir.model.data')
        autofact_id = imd_obj.get_object_reference(
            cursor, uid, 'som_autofactura', 'som_autofactura_task_facturacio'
        )[1]
        task_obj.action_execute_task(cursor, uid, autofact_id, context)

        return {'type': 'ir.actions.act_window_close'}

    def view_tasks(self, cursor, uid, ids, context=None):
        imd_obj = self.pool.get('ir.model.data')
        task_id = imd_obj.get_object_reference(
            cursor, uid, 'som_autofactura', 'som_autofactura_task_facturacio'
        )[1]
        return {
            'domain': "[('task_id','=', {})]".format(task_id),
            'name': _('Tasques de procés automàtic de facturació'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'som.autofactura.task.step',
            'context': {'active_test': False},
            'type': 'ir.actions.act_window',
            'view_id': self.pool.get('ir.ui.view').search(
                        cursor, uid, [
                            ('name', '=', 'som.autofactura.task.step.tree')
                        ],
                        context=context
                    ),

        }

    _columns = {
        'tasks_steps': fields.one2many(
            'wizard.autofactura.task.steps',
            'wiz_auto_id',
            u"Passos de la tasca",
        ),
    }


WizardAutofactura()

class WizardAutofacturaTaskSteps(osv.osv_memory):
    _name = 'wizard.autofactura.task.steps'

    _columns = {
        'step_id': fields.many2one('som.autofactura.task.step', 'TaskStep',
                                      required=True),
        'wiz_auto_id': fields.many2one('wizard.autofactura', 'Passos',
                                  required=True),
        'name': fields.char("Nom", size=30),
        'active': fields.boolean("Estat"),
        'id': fields.integer("id"),
    }
WizardAutofacturaTaskSteps()
