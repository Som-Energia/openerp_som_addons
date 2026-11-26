# -*- coding: utf-8 -*-
from __future__ import absolute_import

import imp
import os

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

    def test_api_key_can_be_updated_without_logging_its_value(self):
        with Transaction().start(self.database) as txn:
            config_id = self.Data.get_object_reference(
                txn.cursor, txn.user, 'som_crawlers', 'demo1_conf'
            )[1]
            self.Configuracio.write(txn.cursor, txn.user, config_id, {
                'api_key': 'old-test-secret',
            })

            self.Configuracio.change_field_value(
                txn.cursor, txn.user, config_id,
                'api_key', 'API-Key', 'new-test-secret',
            )

            config = self.Configuracio.read(
                txn.cursor, txn.user, config_id, ['api_key', 'log']
            )
            self.assertEqual(config['api_key'], 'new-test-secret')
            self.assertIn('API-Key', config['log'])
            self.assertNotIn('old-test-secret', config['log'])
            self.assertNotIn('new-test-secret', config['log'])

    def test_new_ide_api_configurations_default_to_production_url(self):
        with Transaction().start(self.database) as txn:
            for portal in ('iberdrola', 'conquense', 'anselmo'):
                config_id = self.Data.get_object_reference(
                    txn.cursor, txn.user, 'som_crawlers', portal + '_api_conf'
                )[1]
                config = self.Configuracio.read(
                    txn.cursor, txn.user, config_id, ['url_portal', 'crawler']
                )
                self.assertEqual(
                    config['url_portal'], 'https://www.i-de.es/pwelconq/services/arq/'
                )
                self.assertEqual(config['crawler'], 'API')

    def test_ide_credentials_migration_is_idempotent(self):
        migration_path = os.path.join(
            os.path.dirname(__file__), '..', 'migrations', '5.0.25.5.0',
            'post-0006_ADD_ide_api_credentials.py',
        )
        migration = imp.load_source('test_ide_api_credentials_migration', migration_path)
        with Transaction().start(self.database) as txn:
            credentials = {}
            cases = (
                ('iberdrola_api_conf', 'https://wwwd.i-de.es/pwelconq/services/arq/'),
                ('conquense_api_conf', False),
                ('anselmo_api_conf', 'https://wwwd.i-de.es/pwelconq/services/arq'),
            )
            for xml_id, old_url in cases:
                config_id = self.Data.get_object_reference(
                    txn.cursor, txn.user, 'som_crawlers', xml_id
                )[1]
                credentials[config_id] = {
                    'usuari': xml_id + '-user',
                    'contrasenya': xml_id + '-password',
                    'api_key': xml_id + '-key',
                }
                values = dict(credentials[config_id], url_portal=old_url)
                self.Configuracio.write(txn.cursor, txn.user, config_id, values)

            migration.up(txn.cursor, '5.0.25.5.0')
            migration.up(txn.cursor, '5.0.25.5.0')

            for config_id, expected in credentials.items():
                config = self.Configuracio.read(
                    txn.cursor, txn.user, config_id,
                    ['url_portal', 'api_key', 'usuari', 'contrasenya'],
                )
                self.assertEqual(
                    config['url_portal'], 'https://www.i-de.es/pwelconq/services/arq/'
                )
                for field, value in expected.items():
                    self.assertEqual(config[field], value)

                custom_url = 'https://custom.example.test/services/arq/'
                self.Configuracio.write(txn.cursor, txn.user, config_id, {
                    'url_portal': custom_url,
                })

            migration.up(txn.cursor, '5.0.25.5.0')
            for config_id in credentials:
                config = self.Configuracio.read(
                    txn.cursor, txn.user, config_id, ['url_portal']
                )
                self.assertEqual(config['url_portal'], custom_url)

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
            result = self.Configuracio.canviar_contrasenya(
                cursor, uid, crawler_config_id, password
            )
            # check result
            self.assertEqual(result, password)
            # objecte.browse(... + id) per llegir el objecte al complet.
