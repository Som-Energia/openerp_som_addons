# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardScheduleTask(osv.osv_memory):
    _name = 'wizard.schedule.facturacio.task'
    _inherit = 'wizard.schedule.facturacio.task'

    def _get_aviable_tasks(self, cursor, uid, context=None):
        tasks = super(WizardScheduleTask, self)._get_aviable_tasks(
            cursor, uid, context=context
        )

        tasks = [
            (task_code, 'Obrir Factures per workers')
            if task_code == 'obrir_factures_button_by_queue'
            else (task_code, task_label)
            for task_code, task_label in tasks
        ]
        if not any(task_code == 'obrir_factures_button' for task_code, _ in tasks):
            tasks.append(('obrir_factures_button', 'Obrir Factures sequencial'))

        return tasks

    _columns = {
        'tasks': fields.selection(_get_aviable_tasks, 'Tasca', required=True),
    }


WizardScheduleTask()
