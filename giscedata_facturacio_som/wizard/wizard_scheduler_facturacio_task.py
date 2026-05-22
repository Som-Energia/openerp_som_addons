# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from osv import osv, fields


class WizardScheduleTask(osv.osv_memory):
    _name = 'wizard.schedule.facturacio.task'
    _inherit = 'wizard.schedule.facturacio.task'

    def _get_aviable_tasks(self, cursor, uid, context=None):
        tasks = super(WizardScheduleTask, self)._get_aviable_tasks(
            cursor, uid, context=context
        )

        found = False
        for task in tasks:
            if task[0] == 'obrir_factures_button_by_queue':
                task[1] = 'Obrir Factures per workers'
            elif task[0] == 'obrir_factures_button':
                found = True
        if not found:
            tasks.append(('obrir_factures_button', 'Obrir Factures sequencial'))

        return tasks

    _columns = {
        'tasks': fields.selection(_get_aviable_tasks, 'Tasca', required=True),
    }


WizardScheduleTask()
