# -*- coding: utf-8 -*-
from osv import osv
from datetime import datetime

# Describes the module that executes a general task
# @author Ikram Ahdadouche El Idrissi
# @author Dalila Jbilou Kouhous

# Describes the module and contains the function that changes the password


class WizardExecutarTasca(osv.osv_memory):

    # Module name
    _name = "wizard.executar.tasca"

    """Function that gets gets that task, task result and task step, and executes a task  """

    def executar_tasca(self, cursor, uid, ids, context=None):  # tasca individual
        # obtenim l'objecte tasca
        task = self.pool.get("som.crawlers.task")
        if not context:
            return False
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get("active_ids", [])

        for id in active_ids:
            # obtenim una tasca
            task.executar_tasca_async(cursor, uid, id, context)

        return {"type": "ir.actions.act_window_close"}

    def executar_tasca_crawlers_cron(self, cursor, uid, id, context=None):  # tasca cron
        # obtenim l'objecte tasca
        task_obj = self.pool.get("som.crawlers.task")
        active_ids = task_obj.search(cursor, uid, [])
        for id in active_ids:
            # obtenim una tasca
            task = task_obj.browse(cursor, uid, id)
            if not task.data_proxima_execucio:
                task_obj.write(
                    cursor,
                    uid,
                    id,
                    {"data_proxima_execucio": datetime.now().strftime("%Y-%m-%d_%H:%M")},
                )
            if (
                task.data_proxima_execucio
                and datetime.strptime(task.data_proxima_execucio, "%Y-%m-%d %H:%M:%S")
                <= datetime.now()
            ):
                task_obj.executar_tasca_async(cursor, uid, id, context)

        return True


WizardExecutarTasca()
