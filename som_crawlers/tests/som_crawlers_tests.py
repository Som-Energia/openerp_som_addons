## Describes the module(tests) that tests the different functions contained in the project
from destral import testing
from osv import osv
import unittest
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
from datetime import datetime, timedelta
import wizard
import os
# @author Ikram Ahdadouche El Idrissi
# @author Dalila Jbilou Kouhous

## Testing functions

## Module that tests the configutations, specifically passwords
class ConfiguracioTests(testing.OOTestCase):

    ## Functiom that set up all the module dependencies
        # @param self The object pointer

    def setUp(self):
        self.pool = self.openerp.pool
        self.Configuracio = self.pool.get('som.crawlers.config')
        self.Data = self.pool.get('ir.model.data')
        self.task = self.pool.get('som.crawlers.task')
        self.taskStep = self.pool.get('som.crawlers.task.step')
        self.result = self.pool.get('som.crawlers.result')
        self.wiz= self.pool.get('wizard.executar.tasca')

    def tearDown(self):
        pass

    ## Function that tests if the new password is the same as the old one
        # @param self The object pointer
        

    def test_canviarContrasenya_contrasenya_nova_igual_contrasenya_antiga_resultat_exception(self):

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            #get_object_reference per llegir la id de un objecte

            crawler_config_id = self.Data.get_object_reference(cursor, uid, 'som_crawlers', 'demo_configuracio_1')[1]
            #set values
            password = 'Admin'
            #check result
            result = self.Configuracio.canviar_contrasenya(cursor,uid,crawler_config_id,password)
            with self.assertRaises(osv.except_osv) as context:
                self.Configuracio.canviar_contrasenya(cursor,uid,crawler_config_id,password)

            self.assertTrue('Contrasenya identica a la anterior!','Torna a introduir una contrasenya diferent a la anterior' in context.exception)
    ## Function that tests if the modification password gets an ok result
        # @param self The object pointer
    def test_canviarContrasenya_nova_resultat_ok(self):

            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                #get_object_reference per llegir la id de un objecte
                crawler_config_id = self.Data.get_object_reference(cursor, uid, 'som_crawlers', 'demo_configuracio_1')[1]
                #set values
                password = 'Hola'
                #try test
                result = self.Configuracio.canviar_contrasenya(cursor,uid,crawler_config_id,password)
                #check result
                self.assertEqual(result, password)
                #objecte.browse(... + id) per llegir el objecte al complet.


# Module that tests the executar tasca wizard
class WizardExecutarTascaTests(testing.OOTestCase):

    ## Functiom that set up all the module dependencies
        # @param self The object pointer
    def setUp(self):
        self.pool = self.openerp.pool
        self.Configuracio = self.pool.get('som.crawlers.config')
        self.Data = self.pool.get('ir.model.data')
        self.task = self.pool.get('som.crawlers.task')
        self.taskStep = self.pool.get('som.crawlers.task.step')
        self.result = self.pool.get('som.crawlers.result')              
        self.wiz= self.pool.get('wizard.executar.tasca')

    def tearDown(self):
        pass
    
    """Function that tests if after trying to download files, the result is "Falta especificar nom fitxer"
        # @param self The object pointer"""
    def test_download_files_resultat_falta_especificar_nomfitxer(self): #no detecta l'id que toca??

        with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                crawler_task_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_accions_planificades_1')[1]
                crawler_task_step_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_taskStep_3')[1]
                ctx = {
                    'active_id': crawler_task_id, 'active_ids': [crawler_task_id],
                    'from_model':'som.crawlers.task.step'
                 }
                #set values
                result_id = self.result.create(cursor,uid,{'task_id': crawler_task_id,'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M")})
                #try test
                resultat = self.taskStep.download_files(cursor, uid,crawler_task_step_id, result_id,context=ctx)
                #check result
                self.assertEqual(resultat, 'Falta especificar nom fitxer')
               

    """Function that tests if after trying to download files, the result is that the directory does not exits
        # @param self The object pointer"""
    def test_download_files_resultat_file_or_directory_does_not_exist(self):
         with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                crawler_task_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_accions_planificades_1')[1]
                crawler_task_step_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_taskStep_5')[1]
                ctx = {
                    'active_id': crawler_task_id, 'active_ids': [crawler_task_id],
                    'from_model':'som.crawlers.task.step'
                 }
                #set values
                result_id = self.result.create(cursor,uid,{'task_id': id,'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M")})
                #try test
                
                result = self.taskStep.download_files(cursor, uid,crawler_task_step_id,context=ctx)
                #check result
                self.assertEqual(result, 'File or directory doesn\'t exist')
                #objecte.browse(... + id) per llegir el objecte al complet.

    def no_test_download_files_resultat_files_has_been_succesfully_downloaded(self):

        with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                crawler_task_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_accions_planificades_1')[1]
                crawler_task_step_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_taskStep_1')[1]
                ctx = {
                    'active_id': crawler_task_id, 'active_ids': [crawler_task_id],
                    'from_model':'som.crawlers.task.step'
                 }
                #set values
                wiz_id = self.wiz.create(cursor, uid,{},context=ctx)
                #try test
                result = self.wiz.download_files(cursor, uid,crawler_task_step_id,context=ctx)
                #check result
                self.assertEqual(result, 'Files have been successfully downloaded')
                #objecte.browse(... + id) per llegir el objecte al complet.

    #import_xml_files

    """Function that tests if after trying to download an XML file returns that the task step id does not exist
        # @param self The object pointer"""
    def test_import_xml_files_resultat_task_step_id_does_not_exist(self):

            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                crawler_task_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_accions_planificades_2')[1]
                crawler_task_step_id = self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_taskStep_6')[1]
                ctx = {
                    'active_id': crawler_task_id, 'active_ids': [crawler_task_id],
                    'from_model':'som.crawlers.task.step'
                }
                #set values
                wiz_id = self.wiz.create(cursor, uid,{},context=ctx)
                #try test
                result = self.wiz.import_xml_files(cursor, uid,crawler_task_step_id,context=ctx)
                #check result
                self.assertEqual(result, 'don\'t exist id attachment')

    def  no_test_executar_una_tasca(self):

         with Transaction().start(self.database) as txn:

            cursor = txn.cursor
            uid = txn.user
            crawler_task_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_accions_planificades_1')[1]
            ctx = {
                    'active_id': crawler_task_id, 'active_ids': [crawler_task_id],
                    'from_model':'som.crawlers.task.step'
            }
            #set values
            wiz_id = self.wiz.create(cursor, uid,{},context=ctx)
            #try test
            result = self.wiz.executar_tasca(cursor,uid,[wiz_id],context=ctx)
            #check result
            self.assertEqual(result,{'type': 'ir.actions.act_window_close'})

    # id del portal config

    """Function that tests if the portal id configuration returns that anselmo object is ok (demo_taskStep_2)
        # @param self The object pointer"""
    def test_id_del_portal_config_entrada_demo_taskStep_2_sortida_anselmo_objecte_OK(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_config_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_configuracio_1')[1]
            crawler_config_obj = self.Configuracio.browse(cursor,uid,crawler_config_id)
            crawler_task_step_id = self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_taskStep_2')[1]

            result = self.wiz.id_del_portal_config(cursor,uid,crawler_task_step_id)
            self.assertEqual(result,crawler_config_obj)

    """ Function that tests if the id config returns Error (demo_taskStep_2)
        # @param self The object pointer"""
    def test_id_del_portal_config_entrada_demo_taskStep_2_sortida_prova_objecte_Error(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_config_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_configuracio_2')[1]
            crawler_config_obj = self.Configuracio.browse(cursor,uid,crawler_config_id)
            crawler_task_step_id = self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_taskStep_2')[1]

            result = self.wiz.id_del_portal_config(cursor,uid,crawler_task_step_id)
            self.assertNotEqual(result,crawler_config_obj)

    """Function that tests if the attached files zip after giving an inexistent path return that the zip directory does not exist.
        # @param self The object pointer"""
    def test_attach_files_zip_entrada_path_inexistent_sortida_zip_directory_no_existeix(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_config_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_configuracio_2')[1]
            crawler_config_obj = self.Configuracio.browse(cursor,uid,crawler_config_id)
            pathFileActual = os.path.dirname(os.path.realpath(__file__))

            result = self.wiz.attach_files_zip(cursor, uid, id, crawler_config_obj, pathFileActual, context=None)

            self.assertEqual(result,'zip directory doesn\'t exist')

    """Function that tests ifthe attached files zip after giving an empty diretory return that the zip directory is empty.
        # @param self The object pointer"""
    def test_attach_files_zip_entrada_directory_buit_sortida_zip_directory_buit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_config_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_configuracio_1')[1]
            crawler_config_obj = self.Configuracio.browse(cursor,uid,crawler_config_id)
            pathFileActual = os.path.dirname(os.path.realpath(__file__))

            result = self.wiz.attach_files_zip(cursor, uid, id, crawler_config_obj, pathFileActual, context=None)

            self.assertEqual(result,'Directori doesn\'t contain any ZIP')
            
    #funcio no utilitzable

    """def test_attach_files_zip_entrada_config_prova_sortida_files_successfuly_attached(self):  
        with Transaction().start(self.database) as txn:
           # cursor = txn.cursor
            #uid = txn.user
            #crawler_config_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_configuracio_2')[1]
            #crawler_config_obj = self.Configuracio.browse(cursor,uid,crawler_config_id)
            #pathFileActual = os.path.dirname(os.path.realpath(__file__))
            #result = self.wiz.attach_files_zip(cursor, uid, id, crawler_confgi_obj, pathFileActual, context=None)
            #self.assertEqual(result,'files succesfully attached')
    """       
        