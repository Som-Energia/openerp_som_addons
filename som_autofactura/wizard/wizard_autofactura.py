# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class WizardAutofactura(osv.osv_memory):
    _name = 'wizard.autofactura'

    def clean_wizard_auto_task(self, cursor, uid, ids, context=None):
        if isinstance(ids, list):
            ids = ids[0]
        wiz = self.browse(cursor, uid, ids)
        wiz_step_obj = self.pool.get('wizard.autofactura.task.steps')
        wiz_to_delete = wiz_step_obj.search(cursor, uid, [('wiz_auto_id','=',ids)])
        wiz_step_obj.unlink(cursor, uid, wiz_to_delete)

    def update_step_states(self, cursor, uid, ids, context=None):
        import pudb;pu.db
        step_obj = self.pool.get('som.autofactura.task.step')
        wiz_step_obj = self.pool.get('wizard.autofactura.task.steps')
        if isinstance(ids, list):
            ids = ids[0]
        wiz = self.browse(cursor, uid, ids)

        for wiz_step in wiz.tasks_steps:
            #wiz_data = wiz_step_obj.read(cursor, uid, wiz_step)
            step_obj.write(cursor, uid, wiz_step['id'], {'active': wiz_step['active']})
        cursor.commit()
        self.clean_wizard_auto_task(cursor, uid, ids, context)

    def do(self, cursor, uid, ids, context=None):
        task_obj = self.pool.get('som.autofactura.task')
        imd_obj = self.pool.get('ir.model.data')
        autofact_id = imd_obj.get_object_reference(
            cursor, uid, 'som_autofactura', 'som_autofactura_task_facturacio'
        )[1]
        self.update_step_states(cursor, uid, ids, context)
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
            'type': 'ir.actions.act_window',
        }

    def popular(self, cr, uid, ids, context=None):
        # We use default_get as directly assigning the value in defaults like
        # the rest doesn't seem to work for tax (no idea why)
        import pudb;pu.db
        wiz_step_obj = self.pool.get('wizard.autofactura.task.steps')

        imd_obj = self.pool.get('ir.model.data')
        task_id = imd_obj.get_object_reference(
            cr, uid, 'som_autofactura', 'som_autofactura_task_facturacio'
        )[1]
        step_obj = self.pool.get('som.autofactura.task.step')
        step_ids = step_obj.search(cr, uid, [('task_id', '=', task_id)])

        for step_id in step_ids:
            step_data = step_obj.browse(cr, uid, step_id)
            wiz_step_obj.create(cr,uid, {
                'step_id': step_id,
                'wiz_auto_id': ids[0],
                'name': step_data['name'],
                'active': step_data['active'],
                'id': step_data['id'],
            } )
        return True


    def _old_default_get(self, cr, uid, fields_list, context=None):
        # We use default_get as directly assigning the value in defaults like
        # the rest doesn't seem to work for tax (no idea why)
        res = super(WizardAutofactura, self).default_get(
            cr, uid, fields_list, context
        )
        step_obj = self.pool.get('som.autofactura.task.step')
        step_ids = step_obj.search(cr, uid, [('task_id', '=', 1)])
        step_data = step_obj.read(cr, uid, step_ids)
        #import pudb;pu.db
        res.update({
            'tasks_steps': step_data
        })
        for val in res.keys():
            if val not in fields_list:
                del res[val]

        return res

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
