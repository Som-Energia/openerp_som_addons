# -*- coding: utf-8 -*-
##Imports
## Module that contains all the information of a Task
from ast import Param
from inspect import ArgSpec
import pooler
import subprocess
from datetime import datetime, date,timedelta
from osv import osv, fields
from tools.translate import _
import os
import base64
import json
import base64
from fileinput import filename
from genericpath import isfile
import io
from quopri import encodestring
from ssl import DefaultVerifyPaths
import netsvc
import zipfile
from os.path import expanduser

from autoworker import AutoWorker
from oorq.decorators import job

# @author Ikram Ahdadouche El Idrissi
# @author Dalila Jbilou Kouhous

## Class Task that describes the module and the task fields
class SomCrawlersTask(osv.osv):
    ## Module name
    _name = 'som.crawlers.task'
    ## Columns fields
    _columns = {
        'name': fields.char(_(u"Nom"), size=128, help=_("Nom de la tasca"),required=True,),
        'active': fields.boolean( string=_(u"Actiu"), help=_(u"Indica si la tasca està activa o no"),),
        'task_step_ids': fields.one2many('som.crawlers.task.step','task_id', string=_(u"Passos de la tasca")),
        'data_proxima_execucio':fields.datetime(_(u"Data proxima execució"),),
        'configuracio_id': fields.many2one('som.crawlers.config', 'Configuracio', help="Relacio de una configuracio amb la seva tasca",),
        'run_ids': fields.one2many('som.crawlers.result','task_id',string="Llistat d'execucions", help="Llista de execucions que ha realitzat la tasca",),
        'ultima_tasca_executada': fields.char(_(u"Darrer pas executat"), size=128, help=_("Darrer pas de tasca executat"),),
    }
    ## Default values of a column
    _defaults = {
        'active': lambda *a:False,
    }

    def id_del_portal_config(self,cursor,uid,id,context=None):
        classConfig = self.pool.get('som.crawlers.config')
        task_obj = self.browse(cursor,uid,id)
        config_obj = classConfig.browse(cursor,uid,task_obj.configuracio_id.id)
        return config_obj

    @job(queue="som_crawlers_queue")
    def executar_tasca_async(self, cursor, uid, id, context=None):
        self.executar_tasca(cursor, uid, id, context=context)

    def executar_tasca(self,cursor,uid,id,context=None):
        classresult = self.pool.get('som.crawlers.result')
        classTaskStep = self.pool.get('som.crawlers.task.step')
        cron_obj = self.pool.get('ir.cron')
        ir_obj = self.pool.get('ir.model.data')
        task_obj = self.browse(cursor, uid, id)
        task_steps_list = task_obj.task_step_ids
        task_steps_list.sort(key=lambda x: x.sequence)
        result_id = classresult.create(cursor,uid,{'task_id': id,'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M")})
        data_proxima_exec = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        for taskStep in task_steps_list:
            try:
                output = classTaskStep.executar_steps(cursor,uid,taskStep.id,result_id)
                classresult.write(cursor,uid, result_id, {'resultat': output})
            except Exception as e:
                classresult.write(cursor,uid, result_id, {'resultat': str(e)})
                return False

        #seguent data d'execucio
        self.write(cursor, uid, id,{'data_proxima_execucio': data_proxima_exec})
        cron_id = ir_obj.get_object_reference(
            cursor, uid, 'som_crawlers', 'ir_cron_run_tasks_action'
        )[1]
        cron_obj.write(cursor, uid, cron_id, {'nextcall': data_proxima_exec})

SomCrawlersTask()


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

    def executar_steps(self, cursor, uid, id, result_id, context=None):
        taskStep = self.browse(cursor, uid, id)
        function = getattr(self, taskStep.function)
        output = function(cursor, uid, id, result_id, context=None)
        return output


    def attach_files_zip(self, cursor, uid, id, result_id, config_obj, path, context=None):
        classresult = self.pool.get('som.crawlers.result')
        taskStep_obj = self.browse(cursor,uid,id,context = context)
        path_to_zip = os.path.join(path,'tmp/',config_obj.name)
        if not os.path.exists(path_to_zip):
            output = "zip directory doesn\'t exist"
        else:
            if len(os.listdir(path_to_zip)) == 0:
                 output = "Directori doesn\'t contain any ZIP"
            else:
                for fileName in os.listdir(path_to_zip):
                    with open(os.path.join(path_to_zip,fileName), 'rb') as f:
                        content  = f.read()
                    full_path = os.path.join(path_to_zip,fileName)
                    os.remove(full_path)

                    pool = pooler.get_pool(cursor.dbname)
                    attachment = {
                        'name':  fileName,
                        'datas':  base64.b64encode(content),
                        'datas_fname': fileName,
                        'res_model': 'som.crawlers.task',
                        'res_id': taskStep_obj.task_id.id,
                    }

                    attachment_id = self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
                    classresult.write(cursor,uid, result_id, {'zip_name': attachment_id})
                    cursor.commit()
                    output = "files succesfully attached"

        return output

    def download_files(self, cursor, uid,id, result_id, context=None):
        classresult = self.pool.get('som.crawlers.result')
        taskStep_obj = self.browse(cursor,uid,id)
        taskStepParams = json.loads(taskStep_obj.params)
        path = os.path.dirname(os.path.realpath(__file__))

        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M")})

        if taskStepParams.has_key('nom_fitxer'):
            config_obj=self.pool.get('som.crawlers.task').id_del_portal_config(cursor,uid,taskStep_obj.task_id.id,context)
            filePath = os.path.join(path, "scripts/" + taskStepParams['nom_fitxer'])
            if os.path.exists(filePath):
                cfg_obj = self.pool.get('res.config')
                path_python = cfg_obj.get(cursor, uid, 'som_crawlers_massive_importer_python_path', '~/.virtualenvs/massive/bin/python')
                fileName = "output_" + config_obj.name + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M") + ".txt"
                args_str = self.createArgsForScript(cursor, uid, id, config_obj, fileName)
                ret_value = os.system("{} {} {}".format(path_python, filePath, args_str))
                if ret_value != 0:
                    output = "System call from download files failed"
                else:
                    output = self.readOutputFile(cursor, uid, path, fileName)
                if output == 'Files have been successfully downloaded':
                    output = self.attach_files_zip(cursor, uid, id, result_id, config_obj, path, context = context)
                else:
                    raise Exception("%s" % output)
            else:
                output = 'File or directory doesn\'t exist'
        else:
            output = 'Falta especificar nom fitxer'
        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.task_id.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M"))})

        return output

    def import_xml_files(self, cursor, uid, id, result_id, context=None):
        taskStep_obj = self.browse(cursor,uid,id)
        classresult = self.pool.get('som.crawlers.result')
        attachment_obj = self.pool.get('ir.attachment')
        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M")})
        result_obj= classresult.browse(cursor, uid, result_id)
        attachment_id = result_obj.zip_name.id
        if not attachment_id:
            output = "don't exist id attachment"
            raise Exception(output)
        else:
            att = attachment_obj.browse(cursor,uid,attachment_id)
            content = att.datas
            fileName = att.name
            output = self.import_wizard(cursor, uid, fileName,content)

        taskStep_obj.task_id.write({'ultima_tasca_executada': str(taskStep_obj.task_id.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M"))})

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
                if import_wizard.state == 'done':
                    return 'Successful import'
                else:
                    return 'Import error'
            except Exception as e:
                msg = "An error ocurred importing {}:{}".format("asd", "asd")
                return msg
        else:
            return False

    def readOutputFile(self, cursor, uid, path, fileName):
        with open(os.path.join(path,"outputFiles/",fileName)) as f:
            output = f.read().replace('\n', ' ')
        f.close()
        os.remove(os.path.join(path, "outputFiles/",fileName))

        return output

    def createArgsForScript(self, cursor, uid, id, config_obj, fileName):
        str_days = str(config_obj.days_of_margin)
        str_pending = str(config_obj.pending_files_only)
        args = {
            '-n':config_obj.name,
            '-class':config_obj.className,
            '-u':config_obj.usuari,
            '-p':config_obj.contrasenya,
            '-f':fileName,
            '-url':config_obj.url_portal,
            '-fltr':config_obj.filtres,
            '-c':config_obj.crawler,
            '-d':str_days,
            '-nfp':str_pending,
            '-b':config_obj.browser,
        }
        return " ".join(["{} {}".format(k,v) for k,v in args.iteritems()])

SomCrawlersTaskStep()


# Class Result that describes the module and result fields
class SomCrawlersResult(osv.osv):
    # Module name
    _name= 'som.crawlers.result'

    # Column fields
    _columns={

        'name': fields.char(_(u'Funció'), size=64, required=False,),
        'task_id': fields.many2one(
            'som.crawlers.task',
            _('Tasca'),
            help=_('Nom de la tasca'),
            select=True,
        ),
        'data_i_hora_execucio': fields.datetime(
            _(u"Data i hora de l'execució"),),
        'resultat': fields.char(
            _(u"Resultat"),
            help=_("Resultat de l'execució"),
            size=512,),
        'zip_name':fields.many2one('ir.attachment', _(u"Fitxer adjunt"),
        ),

    }
SomCrawlersResult()
