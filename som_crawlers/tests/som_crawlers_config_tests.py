# -*- coding: utf-8 -*-
from destral import testing
from osv import osv
from destral.transaction import Transaction


class ConfiguracioTests(testing.OOTestCase):

    # Functiom that set up all the module dependencies
    # @param self The object pointer

    def setUp(self):
        self.pool = self.openerp.pool
        self.Configuracio = self.pool.get("som.crawlers.config")
        self.Data = self.pool.get("ir.model.data")
        self.task = self.pool.get("som.crawlers.task")
        self.taskStep = self.pool.get("som.crawlers.task.step")
        self.result = self.pool.get("som.crawlers.result")
        self.wiz = self.pool.get("wizard.executar.tasca")

    def tearDown(self):
        pass

    # Function that tests if the new password is the same as the old one
    # @param self The object pointe
    def test_canviarContrasenya_contrasenya_nova_igual_contrasenya_antiga_resultat_exception(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            # get_object_reference per llegir la id de un objecte

            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo1_conf"
            )[1]
            # set values
            password = "Admin"
            # check result
            self.Configuracio.canviar_contrasenya(cursor, uid, crawler_config_id, password)
            with self.assertRaises(osv.except_osv) as context:
                self.Configuracio.canviar_contrasenya(cursor, uid, crawler_config_id, password)

            self.assertTrue(
                "Contrasenya identica a la anterior!",
                "Torna a introduir una contrasenya diferent a la anterior" in context.exception,
            )

    # Function that tests if the modification password gets an ok result
    # @param self The object pointer
    def test_canviarContrasenya_nova_resultat_ok(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            # get_object_reference per llegir la id de un objecte
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo1_conf"
            )[1]
            # set values
            password = "Hola"
            # try test
            result = self.Configuracio.canviar_contrasenya(cursor, uid, crawler_config_id, password)
            # check result
            self.assertEqual(result, password)
            # objecte.browse(... + id) per llegir el objecte al complet.
