from ast import Param
import base64
from fileinput import filename
from quopri import encodestring
import pooler
from osv import osv, fields
from tools.translate import _
import json
import os
from datetime import datetime
import subprocess
import netsvc
import zipfile
from os.path import expanduser

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
                function(cursor,uid,taskStep.id,context)

        return {'type': 'ir.actions.act_window_close'}

    def download_files(self, cursor, uid,id,context=None):
        classresult = self.pool.get('som.crawlers.result')
        classTask = self.pool.get('som.crawlers.task')
        classTaskStep = self.pool.get('som.crawlers.task.step')
        taskStep_obj=classTaskStep.browse(cursor,uid,id)
        taskStepParams = json.loads(taskStep_obj.params)
        path = os.path.dirname(os.path.realpath(__file__))

        if taskStepParams.has_key('nom_fitxer'):
            config_obj=self.id_del_portal_config(cursor,uid,id,context)
            filePath = os.path.join(path, "../scripts/" + taskStepParams['nom_fitxer'])
            path_python = "~/.virtualenvs/massive/bin/python"
            fileName = "output_" + config_obj.name + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M") + ".txt"
            os.system(path_python + " " + filePath + " -n "+ config_obj.name + " -u " + config_obj.usuari + " -p " + config_obj.contrasenya + " -f " + fileName + " -url " + config_obj.url_portal + " -fltr " + config_obj.filtres)
            with open(os.path.join(path,"../outputFiles",fileName)) as f:
                output = f.read().replace('\n', ' ')

            os.remove(os.path.join(path, "../outputFiles/",fileName))
            if output == 'Files have been successfully downloaded':

               self.attach_files(cursor, uid, id, config_obj, path, context = context)

        else:
            output = 'Falta especificar nom fitxer'
        data_i_hora = datetime.now().strftime("%Y-%m-%d_%H:%M")

        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.task_id.name)+ ' - ' + str(data_i_hora)})
        classresult.create(cursor,uid,{'task_id': taskStep_obj.task_id.id, 'data_i_hora_execucio': data_i_hora, 'resultat': output})
        f.close()
        return output

    def id_del_portal_config(self,cursor,uid,id,context=None):
        classresult = self.pool.get('som.crawlers.result')
        classTask = self.pool.get('som.crawlers.task')
        classTaskStep = self.pool.get('som.crawlers.task.step')
        classConfig = self.pool.get('som.crawlers.config')
        task_id = classTaskStep.browse(cursor,uid,id).task_id
        config_id = classTask.browse(cursor,uid,task_id.id).configuracio_id
        config_obj = classConfig.browse(cursor,uid,config_id.id)
        return config_obj

    def attach_files(self, cursor, uid, id, config_obj, path, context=None):

        path_to_zip = os.path.join(path,'../tmp',config_obj.name)
        for fileName in os.listdir(path_to_zip):
            with zipfile.ZipFile(os.path.join(path_to_zip,fileName), 'r') as zip_ref:
                zip_ref.extractall(path_to_zip)
            full_path = os.path.join(path_to_zip,fileName)
            os.remove(full_path)

        for fileName in os.listdir(path_to_zip):
            with open(os.path.join(path_to_zip,fileName), 'rb') as f:
                content = f.read()

            pool = pooler.get_pool(cursor.dbname)
            attachment = {
                'name':  fileName,
                'datas': base64.encodestring(content),
                'datas_fname': fileName,
                'res_model': 'som.crawlers.task',
                'res_id': id,
            }
            self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
            cursor.commit()
            os.remove(os.path.join(path_to_zip,fileName))



WizardExecutarTasca()
