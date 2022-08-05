from destral import testing
from osv import osv
import unittest
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
from datetime import datetime, timedelta
import wizard

class ConfiguracioTests(testing.OOTestCase):

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

    def no_test_canviarContrasenya_contrasenya_nova_igual_contrasenya_antiga_resultat_exception(self):

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

    def no_test_canviarContrasenya_nova_resultat_ok(self):

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


class WizardExecutarTascaTests(testing.OOTestCase):

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

    def no_test_executar_un_fitxer_buida_resultat_falta_especificar_nomFItxer(self): #no detecta l'id que toca??

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
                wiz_id = self.wiz.create(cursor, uid,{},context=ctx)
                #try test
                result = self.wiz.executar_un_fitxer(cursor, uid,crawler_task_step_id,context=ctx)
                #check result
                self.assertEqual(result, 'Falta especificar nom fitxer')
                #objecte.browse(... + id) per llegir el objecte al complet.


    def no_test_executar_un_fitxer_entrada_hol_py_resultat_fitxer_invalid(self): #no detecta l'id que toca??

        with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                crawler_task_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_accions_planificades_1')[1]
                crawler_task_step_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_tasca_1')[1]
                ctx = {
                    'active_id': crawler_task_id, 'active_ids': [crawler_task_id],
                    'from_model':'som.crawlers.task.step'
                 }
                #set values
                wiz_id = self.wiz.create(cursor, uid,{},context=ctx)
                #try test
                result = self.wiz.executar_un_fitxer(cursor, uid,crawler_task_step_id,context=ctx)
                #check result
                self.assertEqual(result, 'File or directory doesn\'t exist')
                #objecte.browse(... + id) per llegir el objecte al complet.

    def no_test_executar_un_fitxer_hola_py_resultat_ok(self):

        with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                crawler_task_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_accions_planificades_1')[1]
                crawler_task_step_id= self.Data.get_object_reference(cursor,uid,'som_crawlers','demo_tasca_2')[1]
                ctx = {
                    'active_id': crawler_task_id, 'active_ids': [crawler_task_id],
                    'from_model':'som.crawlers.task.step'
                 }
                #set values
                wiz_id = self.wiz.create(cursor, uid,{},context=ctx)
                #try test
                result = self.wiz.executar_un_fitxer(cursor, uid,crawler_task_step_id,context=ctx)
                #check result
                self.assertEqual(result, 'ok')
                #objecte.browse(... + id) per llegir el objecte al complet.

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