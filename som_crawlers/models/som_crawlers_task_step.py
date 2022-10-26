# -*- coding: utf-8 -*-
from datetime import datetime
from osv import osv, fields
from tools.translate import _
import json
import os
import pooler
import base64
from time import sleep
from . import som_sftp
import zipfile
import shutil
import StringIO

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

    def get_output_path(self, cursor, uid, context=None):
        cfg_obj = self.pool.get('res.config')
        output_path = cfg_obj.get(cursor, uid, 'som_crawlers_output_tmp_path', '/tmp/outputFiles')
        if not os.path.isdir(output_path):
            os.mkdir(output_path)
        return output_path

    #execute steps of a general task
    def executar_steps(self, cursor, uid, id, result_id, context=None):
        taskStep = self.browse(cursor, uid, id)
        function = getattr(self, taskStep.function)
        output = function(cursor, uid, id, result_id, context=context)
        return output

    def attach_file(self, cursor, uid, path_to_file, file_name, result_id, context=None):
        with open(os.path.join(path_to_file, file_name), 'rb') as f:
            content  = f.read()

        attachment = {
            'name':  file_name,
            'datas':  base64.b64encode(content),
            'datas_fname': file_name,
            'res_model': 'som.crawlers.result',
            'res_id': result_id,
        }
        attachment_id =  self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
        full_path = os.path.join(path_to_file, file_name)
        cursor.commit()
        os.remove(full_path)
        return attachment_id

    #attached files [zip]
    def attach_files_zip(self, cursor, uid, id, result_id, config_obj, path, task_step_params, context=None):
        classresult = self.pool.get('som.crawlers.result')
        task_step_obj = self.browse(cursor,uid,id,context = context)
        output = ''
        if 'process' in task_step_params:
            name = config_obj.name + '_' + task_step_params['process']
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
        task_step_obj = self.browse(cursor,uid,id)
        task_step_params = json.loads(task_step_obj.params)
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M:%S")})
        output = ''

        if task_step_params.has_key('nom_fitxer'):
            config_obj=self.pool.get('som.crawlers.task').id_del_portal_config(cursor,uid,task_step_obj.task_id.id,context)
            script_path = os.path.join(path, "scripts/" + task_step_params['nom_fitxer'])
            if os.path.exists(script_path):
                cfg_obj = self.pool.get('res.config')
                path_python = cfg_obj.get(cursor, uid, 'som_crawlers_massive_importer_python_path', '/home/erp/.virtualenvs/massive/bin/python')
                if not os.path.exists(path_python):
                    raise Exception("Not virtualenv of massive importer found")
                file_name = "output_" + config_obj.name + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M") + ".txt"
                args_str = self.create_script_args(config_obj, task_step_params, file_name)
                ret_value = os.system("{} {} {}".format(path_python, script_path, args_str))
                output_temp_path = self.get_output_path(cursor, uid)
                output = self.readOutputFile(cursor, uid, output_temp_path, file_name)
                if output == 'Files have been successfully downloaded':
                    output = self.attach_files_zip(cursor, uid, id, result_id, config_obj, path, task_step_params, context = context)
                else:
                    self.attach_files_screenshot(cursor, uid, config_obj, path, result_id, context)
                    raise Exception("%s" % output)
            else:
                output = 'File or directory doesn\'t exist'
        else:
            output = 'Falta especificar nom fitxer'
        task_step_obj.task_id.write({'ultima_tasca_executada': str(task_step_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
        classresult.write(cursor, uid, result_id, {'resultat_bool': True})

        return output

    def import_xml_files(self, cursor, uid, id, result_id, nivell=10, context=None):
        if nivell < 0:
            raise Exception("SomCrawlersTaskStep: No s'ha pogut adjuntar el zip")
        task_step_obj = self.browse(cursor,uid,id)
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
                file_name = att.name
                output = self.import_wizard(cursor, uid, file_name, content)
            except:
                sleep(10)
                output = self.import_xml_files(cursor, uid, id, result_id, nivell-1, context)
                return output

        task_step_obj.task_id.write({'ultima_tasca_executada': str(task_step_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
        classresult.write(cursor, uid, result_id, {'resultat_bool': True})

        return output

    def import_ftp_xml_files(self, cursor, uid, id, result_id, context=None):
        try:
            output =  self.import_xml_files(cursor, uid, id, result_id)
        except Exception as e:
            raise Exception("IMPORTANT: " + str(e))
        else:
            task_step_obj = self.browse(cursor,uid,id)
            server_data = self.pool.get('som.crawlers.task').id_del_portal_config(cursor, uid, task_step_obj.task_id.id, context)
            classresult = self.pool.get('som.crawlers.result')
            attachment_obj = self.pool.get('ir.attachment')
            ftp_reg = self.pool.get('som.ftp.file.register')

            result_obj= classresult.browse(cursor, uid, result_id)
            attachment_id = result_obj.zip_name.id
            att = attachment_obj.browse(cursor,uid,attachment_id)

            input_file = att.datas

            working_path = self.get_output_path(cursor, uid) + '/som_crawlers_import_{}'.format(datetime.strftime(datetime.today(), '%Y%m%d%H%M%S'))
            os.makedirs(working_path)

            data = base64.b64decode(input_file)
            file_handler = StringIO.StringIO(data)

            input_file = zipfile.ZipFile(file_handler)
            for filename in input_file.namelist():
                file_id = ftp_reg.search(cursor, uid, [('name','=', filename), ('server_from', '=', server_data['url_portal'])])
                if file_id:
                    ftp_reg.write(cursor, uid, file_id, {'state': 'imported', 'date_imported': datetime.now()})

            shutil.rmtree(working_path)

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

    def readOutputFile(self, cursor, uid, path, file_name):
        try:
            path = os.path.join(path, file_name)
            with open(path) as f:
                output = f.read().replace('\n', ' ')
            f.close()
            os.remove(path)
        except Exception as e:
            return str(e)

        return output

    #test ok
    def create_script_args(self, config_obj, task_step_params, execution_restult_file, file_path=None):
        args = {
            '-n':str(config_obj.name),
            '-u':str(config_obj.usuari),
            '-p':str(config_obj.contrasenya),
            '-c':str(config_obj.crawler),
            '-f':str(execution_restult_file),
            '-url':"'{}'".format(str(config_obj.url_portal)),
            '-url-upload':"'{}'".format(str(config_obj.url_upload)),
            '-fltr':"'{}'".format(str(config_obj.filtres)),
            '-d':str(config_obj.days_of_margin),
            '-nfp':str(config_obj.pending_files_only),
            '-b':str(config_obj.browser),
            '-pr': 'None',
        }
        if file_path:
            args['-fp'] = file_path

        if(task_step_params.has_key('process')):
            args.update({'-pr':str(task_step_params['process'])})

        return " ".join(["{} {}".format(k,v) for k,v in args.iteritems()])


    def upload_files(self, cursor, uid, id, result_id, context=None):
        classresult = self.pool.get('som.crawlers.result')
        task_step_obj = self.browse(cursor,uid,id)
        task_step_params = json.loads(task_step_obj.params)
        config_obj=self.pool.get('som.crawlers.task').id_del_portal_config(cursor,uid,task_step_obj.task_id.id,context)
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
        classresult.write(cursor,uid, result_id, {'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M:%S")})
        #TODO: Que fem quan carreguem el segon fitxer
        path_to_zip = self.get_output_path(cursor, uid)
        file_name = "output_" + config_obj.name + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M") + ".zip"
        file_path = os.path.join(path_to_zip, file_name)
        attachment_id = int(classresult.read(cursor,uid, result_id, ['resultat_text'])['resultat_text'])
        zip_file = self.pool.get('ir.attachment').browse(cursor, uid, attachment_id)
        with open(file_path, 'w') as f:
            f.write(base64.b64decode(zip_file.datas))

        output = ''

        if task_step_params.has_key('nom_fitxer'):
            script_path = os.path.join(path, "scripts/" + task_step_params['nom_fitxer'])
            if os.path.exists(script_path):
                cfg_obj = self.pool.get('res.config')
                path_python = cfg_obj.get(cursor, uid, 'som_crawlers_massive_importer_python_path', '/home/erp/.virtualenvs/massive/bin/python')
                if not os.path.exists(path_python):
                    raise Exception("Not virtualenv of massive importer found")
                execution_restult_file = "output_" + config_obj.name + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M") + ".txt"
                args_str = self.create_script_args(config_obj, task_step_params, execution_restult_file, file_path)
                ret_value = os.system("{} {} {}".format(path_python, script_path, args_str))
                if ret_value != 0:
                    output = "System call from download files failed"
                else:
                    output = self.readOutputFile(cursor, uid, path_to_zip, execution_restult_file)
                if output != 'Files have been successfully uploaded':
                    self.attach_files_screenshot(cursor, uid, config_obj, path, result_id, context)
                    raise Exception("%s" % output)
            else:
                output = 'File or directory doesn\'t exist'
        else:
            output = 'Falta especificar nom fitxer'
        task_step_obj.task_id.write({'ultima_tasca_executada': str(task_step_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
        classresult.write(cursor, uid, result_id, {'resultat_bool': True})
        os.remove(file_path)
        return output

    def export_xml_files(self, cursor, uid, id, result_id, context={}):
        task_step_obj = self.browse(cursor,uid,id)
        sw_obj = self.pool.get('giscedata.switching')
        atr_wiz_obj = self.pool.get('giscedata.switching.wizard')

        task_obj = self.pool.get('som.crawlers.task')
        distri_id = task_obj.read(cursor, uid, task_step_obj.task_id.id, ['distribuidora'])

        task_step_params = json.loads(task_step_obj.params)
        if task_step_params.has_key('process'):
            process = task_step_params['process']
            if not isinstance(process, list):
                process = [process]


        search_params = [('proces_id.name', 'in', process), ('state', '=', 'open'), ('enviament_pendent', '=', True)]
        if distri_id['distribuidora']:
            search_params.append(('partner_id', '=', distri_id['distribuidora'][0]))
        active_ids = sw_obj.search(cursor, uid, search_params)


        if not len(active_ids):
            raise Exception("SENSE RESULTATS: No hi ha fitxers pendents d'exportar")

        ctx = {
            'active_ids': active_ids,
            'active_id': active_ids[0],
        }

        wiz = atr_wiz_obj.create(cursor, uid, {}, context=ctx)
        atr_wiz_obj.action_exportar_xml(cursor, uid, [wiz], context=ctx)
        wiz = atr_wiz_obj.browse(cursor, uid, wiz)

        attachment = {
            'name':  wiz.name,
            'datas':  wiz.file,
            'datas_fname': wiz.name,
            'res_model': 'som.crawlers.result',
            'res_id': result_id,
        }

        attachment_id =  self.pool.get('ir.attachment').create(cursor, uid, attachment, context=context)
        classresult = self.pool.get('som.crawlers.result')
        classresult.write(cursor, uid, result_id, {'zip_name': attachment_id})
        task_step_obj.task_id.write({'ultima_tasca_executada': str(task_step_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
        classresult.write(cursor, uid, result_id, {'resultat_bool': True})

        return attachment_id

    def download_ftp_files(self, cursor, uid, id, result_id, context=None):
        try:
            classresult = self.pool.get('som.crawlers.result')
            ftp_reg = self.pool.get('som.ftp.file.register')
            task_step_obj = self.browse(cursor,uid,id)
            task_step_params = json.loads(task_step_obj.params)
            classresult.write(cursor, uid, result_id, {'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M:%S")})
            output = ''

            if task_step_params.has_key('dir_list'):
                server_data = self.pool.get('som.crawlers.task').id_del_portal_config(cursor, uid, task_step_obj.task_id.id, context)

                base_path = self.get_output_path(cursor, uid)
                temp_folder = server_data['name'] + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
                destination_path = base_path + '/' + temp_folder

                os.mkdir(destination_path)

                #login i anar buscar fitxers al FTP
                sftp = som_sftp.SomSftp()
                sftp.login(server_data)
                file_list, dir_list = sftp.list_files('/', task_step_params['dir_list'])

                #comprovar quins hem de baixar
                files_to_download = []
                for remote_path in file_list:
                    remote_file_name = os.path.basename(remote_path)
                    local_file = ftp_reg.search(cursor, uid, [('name','=', remote_file_name), ('server_from', '=', server_data['url_portal'])])
                    if not local_file or ftp_reg.read(cursor, uid, local_file[0])['state'] != 'imported':
                        files_to_download.append(remote_path)

                if len(files_to_download) == 0:
                    raise Exception("SENSE RESULTATS: No hi ha fitxers a descarregar")

                #descarregar els nous i marcarlos
                files_to_import = []
                for remote_path in files_to_download:
                    try:
                        remote_file_name = os.path.basename(remote_path)
                        sftp.download_file(remote_path, destination_path + '/' + remote_file_name)
                        files_to_import.append(remote_path)
                    except Exception as e:
                        output += str(e) + "\n"
                        file_id = ftp_reg.search(cursor, uid, [('name','=', remote_file_name), ('server_from', '=', server_data['url_portal'])])
                        if file_id:
                            ftp_reg.write(cursor, uid, file_id, {'state': 'error'})
                        else:
                            ftp_reg.create(cursor, uid, {'name': remote_file_name, 'server_from': server_data['url_portal'],
                                'state': 'error', 'date_download': datetime.now()})

                #Fer un zip
                zip_filename = temp_folder + '.zip'
                filenames = os.listdir(destination_path)
                with zipfile.ZipFile(destination_path + '/' + zip_filename, 'w') as zipObj:
                    for filename in filenames:
                        zipObj.write(destination_path + '/' + filename, filename)
                    zipObj.close()

                #attacharlos al result
                attachment_id = self.attach_file(cursor, uid, destination_path, zip_filename, result_id, context)
                classresult.write(cursor, uid, result_id, {'zip_name': attachment_id})
                output = "Fitxer ZIP adjuntat correctament"

                #marcar com a baixats
                for remote_path in files_to_import:
                    remote_file_name = os.path.basename(remote_path)
                    file_id = ftp_reg.search(cursor, uid, [('name','=', remote_file_name), ('server_from', '=', server_data['url_portal'])])
                    if file_id:
                        ftp_reg.write(cursor, uid, file_id, {'state': 'downloaded', 'date_download': datetime.now()})
                    else:
                        ftp_reg.create(cursor, uid, {'name': remote_file_name, 'server_from': server_data['url_portal'],
                                'state': 'downloaded', 'date_download': datetime.now()})

                #esborrar fitxers
                shutil.rmtree(destination_path)

            else:
                output = 'Falta la llista de directoris'

            task_step_obj.task_id.write({'ultima_tasca_executada': str(task_step_obj.name)+ ' - ' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))})
            classresult.write(cursor, uid, result_id, {'resultat_bool': True})
        except Exception as e:
            raise Exception("DESCARREGANT: " + str(e))

        return output


SomCrawlersTaskStep()
