# -*- coding: utf-8 -*-
import json
from destral import testing
from destral.transaction import Transaction
import os


class WizardExecutarTascaTests(testing.OOTestCase):
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

        pathFileActual = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
        os.system("mkdir " + pathFileActual + "/demo/tmp")
        os.system("mkdir " + pathFileActual + "/demo/tmp/anselmo")
        os.system("rm -f " + pathFileActual + "/spiders")
        os.system("mkdir " + pathFileActual + "/spiders")
        os.system("mkdir " + pathFileActual + "/spiders/selenium_spiders")
        os.system("mkdir " + pathFileActual + "/spiders/selenium_spiders/tmp/")
        os.system("mkdir " + pathFileActual + "/spiders/selenium_spiders/tmp/anselmo")

    def tearDown(self):
        pass

    """
    Function that tests if after trying to download files,
    the result is "Falta especificar nom fitxer"
        @param self The object pointer
    """

    def test_download_files_resultat_falta_especificar_nomfitxer(
        self,
    ):  # no detecta l'id que toca??

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_task_step_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_3"
            )[1]
            # set values
            result_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_1"
            )[1]
            # try test
            resultat = self.taskStep.download_files(cursor, uid, crawler_task_step_id, result_id)
            # check result
            self.assertEqual(resultat, "Falta especificar nom fitxer")

    """
    Function that tests if after trying to download files,
    the result is that the directory does not exits
        @param self The object pointer
    """

    def test_download_files_resultat_file_or_directory_does_not_exist(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_task_step_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_5"
            )[1]
            # set values
            result_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_1"
            )[1]
            # try test

            result = self.taskStep.download_files(cursor, uid, crawler_task_step_id, result_id)
            # check result
            self.assertEqual(result, "File or directory doesn't exist")
            # objecte.browse(... + id) per llegir el objecte al complet.

    def no_test_download_files_resultat_files_has_been_succesfully_downloaded(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_task_step_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_1"
            )[1]
            # try test
            result_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_1"
            )[1]
            # try test
            result = self.taskStep.download_files(cursor, uid, crawler_task_step_id, result_id)
            # check result
            self.assertEqual(result, "files succesfully attached")
            # objecte.browse(... + id) per llegir el objecte al complet.

    # import_xml_files
    """Import xml test --> id does not exist
        # @param self The object pointer"""

    def test_import_xml_files_resultat_task_step_id_does_not_exist(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_task_step_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_6"
            )[1]
            result_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_2"
            )[1]
            # try test
            with self.assertRaises(Exception) as context:
                self.taskStep.import_xml_files(cursor, uid, crawler_task_step_id, result_id)
            # check result
            self.assertTrue("Don't exist attachment ID" in context.exception.message)

    def no_test_executar_una_tasca(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_task_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_accions_planificades_1"
            )[1]

            result = self.wiz.executar_tasca(cursor, uid, crawler_task_id, context=None)

            # check result --> comparacio
            self.assertEqual(result, {"type": "ir.actions.act_window_close"})

    # id del portal config
    """ Id portal config tests --> suucessful result
        # @param self The object pointer"""

    def test_id_del_portal_config_entrada_prova_sortida_prova_success(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_task_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_accions_planificades_2"
            )[1]
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "anselmo_conf"
            )[1]
            crawler_config_obj = self.Configuracio.browse(cursor, uid, crawler_config_id)

            result = self.task.id_del_portal_config(cursor, uid, crawler_task_id)

            self.assertEqual(result, crawler_config_obj)

    """ Id portal config tests --> error result
        # @param self The object pointer"""

    def test_id_del_portal_config_entrada_anselmo_sortida_prova_i_error(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_task_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_accions_planificades_1"
            )[1]
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo1_conf"
            )[1]
            crawler_config_obj = self.Configuracio.browse(cursor, uid, crawler_config_id)

            result = self.task.id_del_portal_config(cursor, uid, crawler_task_id)

            self.assertNotEqual(result, crawler_config_obj)

    """Attach file test --> directory does not exist
        # @param self The object pointer"""

    def test_attach_files_zip_entrada_path_inexistent_sortida_zip_directory_no_existeix(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_taskStep_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_1"
            )[1]
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "anselmo_conf"
            )[1]
            result_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_2"
            )[1]
            crawler_config_obj = self.Configuracio.browse(cursor, uid, crawler_config_id)
            pathFileActual = os.path.dirname(os.path.realpath(__file__))
            taskStepParams = {}

            result = self.taskStep.attach_files_zip(
                cursor,
                uid,
                crawler_taskStep_id,
                result_id,
                crawler_config_obj,
                pathFileActual,
                taskStepParams,
                context=None,
            )

            self.assertEqual(result, "zip directory doesn't exist")

    """Attach files zip tests --> directori es buit.
        # @param self The object pointer"""

    def test_attach_files_zip_entrada_directory_buit_sortida_zip_directory_buit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_taskStep_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_1"
            )[1]
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "anselmo_conf"
            )[1]
            result_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_2"
            )[1]
            crawler_config_obj = self.Configuracio.browse(cursor, uid, crawler_config_id)
            empty_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "anselmo")
            current_path = os.path.dirname(os.path.realpath(__file__))
            os.mkdir(empty_path)
            taskStepParams = {}
            result = self.taskStep.attach_files_zip(
                cursor,
                uid,
                crawler_taskStep_id,
                result_id,
                crawler_config_obj,
                current_path,
                taskStepParams,
                context=None,
            )
            os.rmdir(empty_path)
            self.assertEqual(result, "Directori doesn't contain any ZIP")

    """ Attach files zip test --> file successfully attached
        # @param self The object pointer"""

    def test_attach_files_zip_entrada_config_prova_sortida_files_successfuly_attached(
        self,
    ):  # si que dona ok, pero al no tenir el zip donara fail pq fem remove
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            result_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_3"
            )[1]
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "anselmo_conf"
            )[1]
            crawler_taskStep_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_8"
            )[1]
            crawler_config_obj = self.Configuracio.browse(cursor, uid, crawler_config_id)
            pathFileActual = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
            path_desti = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmpDir")
            create_path = os.path.join(path_desti, "anselmo")
            if not os.path.exists(create_path):
                os.mkdir(path_desti)
                os.mkdir(create_path)
            os.system(
                "cp "
                + pathFileActual
                + "/demo/anselmo_2022-07-26_15_11_GRCW_W4X151_20220726151137.zip "
                + path_desti
                + "/anselmo/anselmo_2022-07-26_15_11_GRCW_W4X151_20220726151137.zip"
            )
            taskStepParams = {}

            result = self.taskStep.attach_files_zip(
                cursor,
                uid,
                crawler_taskStep_id,
                result_id,
                crawler_config_obj,
                path_desti,
                taskStepParams,
                context=None,
            )

            self.assertEqual(
                result,
                "File anselmo_2022-07-26_15_11_GRCW_W4X151_20220726151137.zip succesfully attached\n",  # noqa: E501
            )

    """  Create args for script test --> sortida string arguments
         # @param self The object pointer"""

    def test__create_script_args__entrada_config_prova_sortida_string_arguments(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo1_conf"
            )[1]
            crawler_taskStep_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_9"
            )[1]
            taskStep_obj = self.taskStep.browse(cursor, uid, crawler_taskStep_id)
            taskStepParams = json.loads(taskStep_obj.params)
            crawler_config_obj = self.Configuracio.browse(cursor, uid, crawler_config_id)
            fileName = "prova.txt"

            result = self.taskStep.create_script_args(crawler_config_obj, taskStepParams, fileName)

            result_string = "-pr None -u usuariProva -d 80 -f prova.txt -url 'https://egymonluments.gov.eg/en/museums/egyptian-museum' -p contraProva -c Selenium -b firefox -n prova1 -fltr 'https://egymonuments.gov.eg/en/collections/kawit-sarcophagus-4' -nfp False -url-upload 'False'"  # noqa: E501
            self.assertEqual(set(result.split()), set(result_string.split()))

    def test__create_script_args__entrada_config_prova_mes_context_sortida_string_arguments_mes_context(self):  # noqa: E501
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            crawler_config_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo1_conf"
            )[1]
            crawler_taskStep_id = self.Data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_taskStep_9"
            )[1]
            taskStep_obj = self.taskStep.browse(cursor, uid, crawler_taskStep_id)
            taskStepParams = json.loads(taskStep_obj.params)
            crawler_config_obj = self.Configuracio.browse(cursor, uid, crawler_config_id)
            fileName = "prova.txt"
            test = {"codi_municipi": "1234567", "filepath": "here/there/file.xml"}
            result = self.taskStep.create_script_args(
                crawler_config_obj, taskStepParams, fileName, context=test)

            result_string = """-pr None -u usuariProva -d 80 -f prova.txt -url 'https://egymonluments.gov.eg/en/museums/egyptian-museum' -p contraProva -c Selenium -b firefox -n prova1 -fltr 'https://egymonuments.gov.eg/en/collections/kawit-sarcophagus-4' -nfp False -url-upload 'False' -context '{"codi_municipi": "1234567", "filepath": "here/there/file.xml"}'"""  # noqa: E501
            self.assertEqual(set(result.split()), set(result_string.split()))

    def test_readOutPutFile_entrada_path_inexistent_sortida_excepcio(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            path = "~/hola"
            filename = "porva.zip"

            result = self.taskStep.readOutputFile(cursor, uid, path, filename)

            self.assertEqual(
                "[Errno 2] No such file or directory: '" + path + "/" + filename + "'", result
            )

    def test_readOutPutFile_entrada_path_zip_demo_2_sortida_ok(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../demo/tmp")
            filename = "anselmo_2022-07-26_15_11_GRCW_W4X151_20220726151137.zip"
            os.system(
                "cp "
                + path
                + "/../anselmo_2022-07-26_15_11_GRCW_W4X151_20220726151137.zip "
                + path
                + "/anselmo_2022-07-26_15_11_GRCW_W4X151_20220726151137.zip"
            )

            result = self.taskStep.readOutputFile(cursor, uid, path, filename)

            self.assertNotEqual(
                "[Errno 2] No such file or directory: '" + path + "/" + filename + "'", result
            )
