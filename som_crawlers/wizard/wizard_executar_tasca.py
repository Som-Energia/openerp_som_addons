from ast import Param
import base64
from fileinput import filename
from genericpath import isfile
from quopri import encodestring
from ssl import DefaultVerifyPaths
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
        classresult = self.pool.get('som.crawlers.result')
        classTaskStep = self.pool.get('som.crawlers.task.step')
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
                taskStep_obj=classTaskStep.browse(cursor,uid,taskStep.id)
                result_id = classresult.create(cursor,uid,{'task_id': taskStep_obj.task_id.id, 'name': taskStep_obj.name})
                function(cursor,uid,taskStep.id, result_id, taskStep_obj, context)

        return {'type': 'ir.actions.act_window_close'}

    def download_files(self, cursor, uid,id, result_id, taskStep_obj, context=None):

        classresult = self.pool.get('som.crawlers.result')
        taskStepParams = json.loads(taskStep_obj.params)
        path = os.path.dirname(os.path.realpath(__file__))

        if taskStepParams.has_key('nom_fitxer'):
            config_obj=self.id_del_portal_config(cursor,uid,taskStep_obj,context)
            filePath = os.path.join(path, "../scripts/" + taskStepParams['nom_fitxer'])
            if os.path.exists(filePath):
                path_python = "~/.virtualenvs/massive/bin/python"
                fileName = "output_" + config_obj.name + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M") + ".txt"
                os.system(path_python + " " + filePath + " -n "+ config_obj.name + " -u " + config_obj.usuari + " -p " + config_obj.contrasenya + " -f " + fileName + " -url " + config_obj.url_portal + " -fltr " + config_obj.filtres + " -c " + config_obj.crawler + " -d " + str(config_obj.days_of_margin) + " -nfp " + str(config_obj.pending_files_only) + " -b " + config_obj.browser) 

                with open(os.path.join(path,"../outputFiles",fileName)) as f:
                    output = f.read().replace('\n', ' ')

                os.remove(os.path.join(path, "../outputFiles",fileName))
                if output == 'Files have been successfully downloaded':
                    output = self.attach_files_zip(cursor, uid, id, result_id, config_obj, taskStep_obj, path, context = context)

                f.close()
            else:
                output = 'File or directory doesn\'t exist'
        else:
            output = 'Falta especificar nom fitxer'

        data_i_hora = datetime.now().strftime("%Y-%m-%d_%H:%M")
        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.task_id.name)+ ' - ' + str(data_i_hora)})
        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': data_i_hora, 'resultat': output})

        return output

    def import_xml_files(self, cursor, uid,id, result_id, taskStep_obj, context=None):

        classresult = self.pool.get('som.crawlers.result')
        attachment_obj = self.pool.get('ir.attachment')
        
        data_i_hora = datetime.now().strftime("%Y-%m-%d_%H:%M")
        #attachment_id = attachment_obj.search(cursor, uid, [('res_model',"=",'som.crawlers.task'),('res_id', "=", taskStep_obj.task_id.id)])
       
       
        id_last_result= classresult.search(cursor, uid, [('task_id','=', taskStep_obj.task_id.id),('name', '=', 'Descarregar fitxers'),('data_i_hora_execucio', '=', data_i_hora),('resultat', '=', 'files succesfully attached')])
        last_result_obj= classresult.browse(cursor, uid, id_last_result)
        attachment_id = last_result_obj[0].zip_name.id
        if not attachment_id:
            output = "don't exist id attachment"

        else:
            att = attachment_obj.browse(cursor,uid,attachment_id)
            content = att.datas
            fileName = att.name

            output = self.import_wizard(cursor, uid, fileName, base64.b64encode(bytes(content)))

        data_i_hora = datetime.now().strftime("%Y-%m-%d_%H:%M")
        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.task_id.name)+ ' - ' + str(data_i_hora)})
        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': data_i_hora, 'resultat': output})
        return output

    def id_del_portal_config(self,cursor,uid,taskStep_obj,context=None):

        classTask = self.pool.get('som.crawlers.task')
        classConfig = self.pool.get('som.crawlers.config')
        task_id = taskStep_obj.task_id.id
        config_id = classTask.browse(cursor,uid,task_id).configuracio_id.id
        config_obj = classConfig.browse(cursor,uid,config_id)
        return config_obj


    def attach_files_zip(self, cursor, uid, id, result_id, config_obj, taskStep_obj, path, context=None):
        classresult = self.pool.get('som.crawlers.result')
        path_to_zip = os.path.join(path,'../tmp',config_obj.name)
        if not os.path.exists(path_to_zip):
            output = "zip directory doesn\'t exist"
        else:
            if len(os.listdir(path_to_zip)) == 0:
                 output = "Directori doesn\'t contain any ZIP"
            else:
                for fileName in os.listdir(path_to_zip):
                    with open(os.path.join(path_to_zip,fileName), 'r') as f:
                        content  = f.read()
                    full_path = os.path.join(path_to_zip,fileName)
                    os.remove(full_path)

                    pool = pooler.get_pool(cursor.dbname)

                    attachment = {
                        'name':  fileName,
                        'datas':  base64.encodestring(content),
                        'datas_fname': fileName,
                        'res_model': 'som.crawlers.task',
                        'res_id': taskStep_obj.task_id.id,
                    }

                    attachment_id = self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
                    classresult.write(cursor,uid, result_id, {'zip_name': attachment_id})
                    cursor.commit()
                    output = "files succesfully attached"

        return output

    def attach_files_xml(self, cursor, uid, id, config_obj, path, context=None):

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
                'datas':  base64.encodestring(content),
                'datas_fname': fileName,
                'res_model': 'som.crawlers.task',
                'res_id': id,
            }
            self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
            cursor.commit()
            os.remove(os.path.join(path_to_zip,fileName))


    def import_wizard(self, cursor, uid, file_name, file_content):
        if file_name.endswith('.zip'):
            file_content = base64.decodestring(file_content)
            values = {'filename': file_name, 'file': base64.b64encode(file_content).decode()}
            WizardImportAtrF1 = self.pool.get('wizard.import.atr.and.f1')
            import_wizard_id = WizardImportAtrF1.create(cursor,uid,values)
            import_wizard  = WizardImportAtrF1.browse(cursor, uid, import_wizard_id)
            context = {'active_ids': [import_wizard.id], 'active_id': import_wizard.id}

            try:
                import pudb;pu.db
                import_wizard.action_import_xmls(cursor, uid, context)
                if import_wizard.state == 'load':
                    import_wizard.action_send_xmls(cursor, uid, context=context)
                if import_wizard.state == 'done':
                    return 'Successful import'
                else:
                    return 'Import error'
            except Exception as e:
                msg = "An error ocurred importing %s: %s"
                return msg
        else:
            return False

WizardExecutarTasca()
