from destral import testing
from osv import osv
import unittest
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
from datetime import datetime, timedelta

class ConfiguracioTests(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.Configuracio = self.pool.get('som.crawlers.config')
        self.Data = self.pool.get('ir.model.data')

    def tearDown(self):
        pass

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
