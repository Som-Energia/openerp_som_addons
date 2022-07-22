from ast import Param
from osv import osv, fields
from tools.translate import _
import json
import os
from datetime import datetime
import subprocess
import netsvc

LOGGER = netsvc.Logger()

class WizardExecutarTasca(osv.osv_memory):
    _name= 'wizard.executar.tasca'

    def executar_tasca(self, cursor, uid, ids, context=None):
        #obtenim l'objecte tasca
        task = self.pool.get('som.crawlers.task')


        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get('active_ids',[])

        for id in active_ids:
            #obtenim una tasca
            task_obj = task.browse(cursor, uid, id)
            task_steps_list = task_obj.task_step_ids
            task_steps_list.sort(key=lambda x: x.sequence)
            for taskStep in task_steps_list:
                function = getattr(self, taskStep.function)
                function(cursor,uid,id,context)

        return {'type': 'ir.actions.act_window_close'}

    def executar_un_fitxer(self, cursor, uid,id,context=None):
        classresult = self.pool.get('som.crawlers.result')
        classTask = self.pool.get('som.crawlers.task')
        classTaskStep = self.pool.get('som.crawlers.task.step')
        taskStep_obj=classTaskStep.browse(cursor,uid,id)
        taskStepParams = json.loads(taskStep_obj.params)
        if taskStepParams.has_key('nom_fitxer'):
            output =os.system("python3 /home/somenergia/src/openerp_som_addons/som_crawlers/som_crawlers/Downloads/"
             + taskStepParams['nom_fitxer'])
            if output == 0:
                output = 'ok'
            elif output == 512:
                output = 'File or directory doesn\'t exist'
            else :
                output = 'Error while executing'

        else:
            output = 'Falta especificar nom fitxer'
        data_i_hora = datetime.now()
        classresult.create(cursor,uid,{'task_id': taskStep_obj.task_id.id, 'data_i_hora_execucio': data_i_hora, 'resultat':output})
        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.task_id.name)+ ' - ' + str(data_i_hora)})
        return output





WizardExecutarTasca()