# -*- coding: utf-8 -*-
from datetime import datetime
from osv import osv, fields
from tools.translate import _
import json
import os
import pooler
import base64
from time import sleep


# Class Task Step that describes the module and the task step fields
class SomCrawlersTaskStep(osv.osv):

    # Module name
    _name = 'som.crawlers.task.step'
    _order = 'sequence'
    # Column fields
    _columns = {
        'name': fields.char(
            _(u"Nom"),
            help=_("Nom del pas"),
            size=128,
            required=True,
        ),
        'sequence': fields.integer(
            _(u'Ordre'),
            required=True,
        ),
        'function': fields.char(
            _(u'Funció'),
            help=_("Funció del model a executar"),
            size=256,
            required=True,
        ),
        'params': fields.text(
            _(u"Paràmetres"),
            help=_("Parametres a passar a la funció del model a executar"),
        ),
        'task_id': fields.many2one(
            'som.crawlers.task',
            _('Tasca'),
            help=_("Tasca englobant"),
            select=True,
        ),
    }

    # Default values of a column
    _defaults = {
        'sequence': lambda *a: 99,
        'function': lambda *a: '',
        'name': lambda *a: 'nom_per_defecte',
    }

    #execute steps of a general task
    def executar_steps(self, cursor, uid, id, result_id, context=None):
        taskStep = self.browse(cursor, uid, id)
        function = getattr(self, taskStep.function)
        output = function(cursor, uid, id, result_id, context=None)
        return output

    def attach_file(self, cursor, uid, path_to_file, file_name, result_id, context=None):
        with open(os.path.join(path_to_file,file_name), 'rb') as f:
            content  = f.read()

        attachment = {
            'name':  file_name,
            'datas':  base64.b64encode(content),
            'datas_fname': file_name,
            'res_model': 'som.crawlers.result',
            'res_id': result_id,
        }
        attachment_id =  self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
        full_path = os.path.join(path_to_file,file_name)
        cursor.commit()
        os.remove(full_path)
        return attachment_id

    #attached files [zip]
    def attach_files_zip(self, cursor, uid, id, result_id, config_obj, path, taskStepParams, context=None):
        classresult = self.pool.get('som.crawlers.result')
        taskStep_obj = self.browse(cursor,uid,id,context = context)
        output = ''
        if 'process' in taskStepParams:
            name = config_obj.name + '_' + taskStepParams['process']
            path_to_zip = os.path.join(path,'spiders/selenium_spiders/tmp/', name)
        else:
           path_to_zip = os.path.join(path,'spiders/selenium_spiders/tmp/', config_obj.name)
        if not os.path.exists(path_to_zip):
            output = "zip directory doesn\'t exist"
        else:
            if len(os.listdir(path_to_zip)) == 0:
                 output = "Directori doesn\'t contain any ZIP"
            else:
                for file_name in os.listdir(path_to_zip):
                    attachment_id = self.attach_file(cursor, uid, path_to_zip, file_name, result_id, context)
                    classresult.write(cursor,uid, result_id, {'zip_name': attachment_id})
                    output = "files succesfully attached"
        return output

    def attach_files_screenshot(self, cursor, uid, config_obj, path, result_id, context=None):
        path_to_screenshot = os.path.join(path,'spiders/selenium_spiders/screenShots/' + config_obj.name)
        if os.path.exists(path_to_screenshot):
            for file_name in os.listdir(path_to_screenshot):
                self.attach_file(cursor, uid, path_to_screenshot, file_name, result_id, context)

    def download_files(self, cursor, uid,id, result_id, context=None):
        classresult = self.pool.get('som.crawlers.result')
        taskStep_obj = self.browse(cursor,uid,id)
        taskStepParams = json.loads(taskStep_obj.params)
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M:%S")})
        output = ''

        if taskStepParams.has_key('nom_fitxer'):
            config_obj=self.pool.get('som.crawlers.task').id_del_portal_config(cursor,uid,taskStep_obj.task_id.id,context)
            filePath = os.path.join(path, "scripts/" + taskStepParams['nom_fitxer'])
            if os.path.exists(filePath):
                cfg_obj = self.pool.get('res.config')
                path_python = cfg_obj.get(cursor, uid, 'som_crawlers_massive_importer_python_path', '/home/erp/.virtualenvs/massive/bin/python')
                if not os.path.exists(path_python):
                    raise Exception("Not virtualenv of massive importer found")
                fileName = "output_" + config_obj.name + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M") + ".txt"
                args_str = self.createArgsForScript(config_obj, taskStepParams, fileName)
                ret_value = os.system("{} {} {}".format(path_python, filePath, args_str))
                if ret_value != 0:
                    output = "System call from download files failed"
                else:
                    pathToZip = '/tmp/outputFiles'
                    output = self.readOutputFile(cursor, uid, pathToZip, fileName)
                if output == 'Files have been successfully downloaded':
                    output = self.attach_files_zip(cursor, uid, id, result_id, config_obj, path, taskStepParams, context = context)
                else:
                    self.attach_files_screenshot(cursor, uid, config_obj, path, result_id, context)
                    raise Exception("%s" % output)
            else:
                output = 'File or directory doesn\'t exist'
        else:
            output = 'Falta especificar nom fitxer'
        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
        classresult.write(cursor, uid, result_id, {'resultat_bool': True})

        return output

    def import_xml_files(self, cursor, uid, id, result_id, nivell=10, context=None):
        if nivell < 0:
            raise Exception("SomCrawlersTaskStep: No s'ha pogut adjuntar el zip")

        taskStep_obj = self.browse(cursor,uid,id)
        classresult = self.pool.get('som.crawlers.result')
        attachment_obj = self.pool.get('ir.attachment')
        classresult.write(cursor, uid, result_id, {'resultat_bool': False})
        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M:%S")})
        result_obj= classresult.browse(cursor, uid, result_id)
        attachment_id = result_obj.zip_name.id
        if not attachment_id:
            output = "don't exist id attachment"
            raise Exception(output)
        else:
            try:
                att = attachment_obj.browse(cursor,uid,attachment_id)
                content = att.datas
                fileName = att.name
                output = self.import_wizard(cursor, uid, fileName,content)
            except:
                sleep(10)
                output = self.import_xml_files(cursor, uid, id, result_id, nivell-1, context)
                return output

        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
        classresult.write(cursor, uid, result_id, {'resultat_bool': True})

        return output

    def import_wizard(self, cursor, uid, file_name, file_content):
        if file_name.endswith('.zip'):
            values = {'filename': file_name, 'file': file_content}
            WizardImportAtrF1 = self.pool.get('wizard.import.atr.and.f1')
            import_wizard_id = WizardImportAtrF1.create(cursor,uid,values)
            import_wizard  = WizardImportAtrF1.browse(cursor, uid, import_wizard_id)
            context = {'active_ids': [import_wizard.id], 'active_id': import_wizard.id}

            try:
                import_wizard.action_import_xmls(context)
                if import_wizard.state == 'load':
                    import_wizard.action_send_xmls(context=context)
                return WizardImportAtrF1.browse(cursor, uid, import_wizard_id).info
            except Exception as e:
                msg = "An error ocurred importing {}:{}".format("asd", "asd")
                return msg
        else:
            return False

    def readOutputFile(self, cursor, uid, path, fileName):
        try:
            path = os.path.join(path,fileName)
            with open(path) as f:
                output = f.read().replace('\n', ' ')
            f.close()
            os.remove(path)
        except Exception as e:
            return str(e)

        return output

    #test ok
    def createArgsForScript(self,config_obj, taskStepsParams,fileName):
        args = {
            '-n':str(config_obj.name),
            '-u':str(config_obj.usuari),
            '-p':str(config_obj.contrasenya),
            '-c':str(config_obj.crawler),
            '-f':str(fileName),
            '-url':"'{}'".format(str(config_obj.url_portal)),
            '-fltr':"'{}'".format(str(config_obj.filtres)),
            '-d':str(config_obj.days_of_margin),
            '-nfp':str(config_obj.pending_files_only),
            '-b':str(config_obj.browser),
            '-pr': 'None',
        }
        if(taskStepsParams.has_key('process')):
            args.update({'-pr':str(taskStepsParams['process'])})

        return " ".join(["{} {}".format(k,v) for k,v in args.iteritems()])


    def upload_files(self, cursor, uid):
        pass

    def export_xml_files(self, cursor, uid, id, result_id, proces_name='D1', step_name='02', context={}):
        sw_obj = self.pool.get('giscedata.switching')
        atr_wiz_obj = self.pool.get('giscedata.switching.wizard')
        task_step_obj = self.browse(cursor,uid,id)
        active_ids = sw_obj.search(cursor, uid, [('proces_id.name','=', proces_name),
            ('step_id.name','=', step_name), ('state','=', 'open')])
        ctx = {
            'active_ids': active_ids,
            'active_id': active_ids[0],
        }
        wiz = atr_wiz_obj.create(cursor, uid, {}, context=ctx)
        atr_wiz_obj.action_exportar_xml(cursor, uid, [wiz], context=ctx)
        wiz = atr_wiz_obj.browse(cursor, uid, wiz)

        attachment = {
            'name':  wiz.name,
            'datas':  base64.b64encode(wiz.file),
            'datas_fname': wiz.name,
            'res_model': 'som.crawlers.result',
            'res_id': result_id,
        }
        attachment_id =  self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
        classresult = self.pool.get('som.crawlers.result')
        classresult.write(cursor,uid, result_id, {'zip_name': attachment_id})
        task_step_obj.task_id.write({'ultima_tasca_executada': str(task_step_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
        classresult.write(cursor, uid, result_id, {'resultat_bool': True})
        pass

SomCrawlersTaskStep()
