# -*- coding: utf-8 -*-

from destral.transaction import Transaction
from giscedata_switching.tests.common_tests import TestSwitchingImport
from addons import get_module_resource
from datetime import datetime
import mock
import giscedata_atc_switching


class TestUnlinkATC(TestSwitchingImport):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test__unlink_one_ATC__cancelATC(self):
        """
        Test per comprovar que l'unlink no elimina i cancela el cas
        """

        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]
        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc.unlink()

        self.assertEqual(atc.state, "cancel")

    def test__case_cancel_ATC_without_R1associat__cancelATC(self):
        """
        Test case_cancel for atc without R1 associat ATC is cancelled
        """

        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]
        atc_o.write(self.cursor, self.uid, atc_id, {"state": "open"})

        atc_o.case_cancel(self.cursor, self.uid, atc_id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "cancel")

    def test__case_cancel_ATC_with_R101_enviament_pendentFalse__NoCancelATC(self):
        """
        Test case_cancel for atc 'pending' with R101 without enviament_pendent, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor, self.uid, atc_id, {"state": "pending", "ref": "giscedata.switching,1"}
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 01 està pendent del pas finalitzador".format(
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "pending")

    def test__case_cancel_ATC_with_R101_enviament_pendentTrue__CancelATC(self):
        """
        Test case_cancel for atc 'pending' with R101 with enviament_pendent, ATC is cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        self.switch(self.txn, "comer")
        contract_id = self.get_contract_id(self.txn)

        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "01")

        step_obj = self.openerp.pool.get("giscedata.switching.r1.01")
        sw_obj = self.openerp.pool.get("giscedata.switching")
        r101 = step_obj.browse(self.cursor, self.uid, step_id)
        sw_id = sw_obj.browse(self.cursor, self.uid, r101.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "pending", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        r101.write({"enviament_pendent": True})

        atc_o.case_cancel(self.cursor, self.uid, atc_id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "cancel")

    @mock.patch.object(giscedata_atc_switching.giscedata_atc.GiscedataAtc, "has_r1_no_finalitzat")
    def test__case_cancel_ATC_with_R102_no_finalizat__NOCancelATC(self, mock_has_r1_no_finalitzat):
        """
        Test case_cancel for atc 'open' with R102 no finalitzat, ATC is not cancelled
        """
        mock_has_r1_no_finalitzat.return_value = False

        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r102_new.xml"
        )

        self.switch(self.txn, "comer")

        r101_obj = self.openerp.pool.get("giscedata.switching.r1.01")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-01
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "01")

        r101 = r101_obj.browse(self.cursor, self.uid, step_id)
        sw_obj.write(self.cursor, self.uid, r101.sw_id.id, {"codi_sollicitud": "201602231255"})
        # El creem ara perque la data sigui posterior a la posada al r101
        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        sw_obj.importar_xml(self.cursor, self.uid, r1_xml, "r102.xml")
        sw_id = sw_obj.browse(self.cursor, self.uid, r101.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            u"Cas ATC {} no es pot cancel·lar: R1 02 l'heu de revisar i tancar".format(atc_id),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

    @mock.patch.object(giscedata_atc_switching.giscedata_atc.GiscedataAtc, "has_r1_no_finalitzat")
    def test__case_cancel_ATC_with_R102_finalizat__NOCancelATC(self, mock_has_r1_no_finalitzat):
        """
        Test case_cancel for atc 'open' with R102 finalitzat, ATC is not cancelled
        """
        mock_has_r1_no_finalitzat.return_value = True

        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r102_new.xml"
        )

        self.switch(self.txn, "comer")

        r101_obj = self.openerp.pool.get("giscedata.switching.r1.01")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-01
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "01")

        r101 = r101_obj.browse(self.cursor, self.uid, step_id)
        sw_obj.write(self.cursor, self.uid, r101.sw_id.id, {"codi_sollicitud": "201602231255"})
        # El creem ara perque la data sigui posterior a la posada al r101
        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        sw_obj.importar_xml(self.cursor, self.uid, r1_xml, "r102.xml")
        sw_id = sw_obj.browse(self.cursor, self.uid, r101.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            u"Cas ATC {} no es pot cancel·lar: R1 02 està pendent del pas finalitzador".format(
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

    def test__case_cancel_ATC_with_R103__NOCancelATC(self):
        """
        Test case_cancel for atc 'open' or 'pending' with R103, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r103_new.xml"
        )
        with open(r1_xml_path, "r") as f:
            r103_xml = f.read()

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r102_new.xml"
        )
        with open(r1_xml_path, "r") as f:
            r102_xml = f.read()

        self.switch(self.txn, "comer")

        r101_obj = self.openerp.pool.get("giscedata.switching.r1.01")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-01
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "01")

        r101 = r101_obj.browse(self.cursor, self.uid, step_id)
        sw_obj.write(self.cursor, self.uid, r101.sw_id.id, {"codi_sollicitud": "201602231255"})
        # El creem ara perque la data sigui posterior a la posada al r101
        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        sw_obj.importar_xml(self.cursor, self.uid, r102_xml, "r102.xml")
        sw_obj.importar_xml(self.cursor, self.uid, r103_xml, "r103.xml")

        sw_id = sw_obj.browse(self.cursor, self.uid, r101.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value, "Cas ATC {} no es pot cancel·lar: R1 03 en estat Obert".format(atc_id)
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "pending", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 03 està pendent del pas finalitzador".format(
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "pending")

    def test__case_cancel_ATC_with_R104__NOCancelATC(self):
        """
        Test case_cancel for atc 'open' or 'pending' with R104, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        self.switch(self.txn, "comer")
        contract_id = self.get_contract_id(self.txn)

        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "04")

        step_obj = self.openerp.pool.get("giscedata.switching.r1.04")
        sw_obj = self.openerp.pool.get("giscedata.switching")
        r104 = step_obj.browse(self.cursor, self.uid, step_id)
        sw_id = sw_obj.browse(self.cursor, self.uid, r104.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 04 en estat Obert - ERROR MANUAL -".format(atc_id),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "pending", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value, "Cas ATC {} no es pot cancel·lar: R1 04 en estat Pendent".format(atc_id)
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "pending")

    def test__case_cancel_ATC_with_R105__NOCancelATC(self):
        """
        Test case_cancel for atc 'open' with R105, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r105_new.xml"
        )
        with open(r1_xml_path, "r") as f:
            r105_xml = f.read()

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r102_new.xml"
        )
        with open(r1_xml_path, "r") as f:
            r102_xml = f.read()

        self.switch(self.txn, "comer")

        r101_obj = self.openerp.pool.get("giscedata.switching.r1.01")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-01
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "01")

        r101 = r101_obj.browse(self.cursor, self.uid, step_id)
        sw_obj.write(self.cursor, self.uid, r101.sw_id.id, {"codi_sollicitud": "201602231255"})
        # El creem ara perque la data sigui posterior a la posada al r101
        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        sw_obj.importar_xml(self.cursor, self.uid, r102_xml, "r102.xml")
        sw_obj.importar_xml(self.cursor, self.uid, r105_xml, "r105.xml")

        sw_id = sw_obj.browse(self.cursor, self.uid, r101.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 05 l'heu de revisar i tancar".format(atc_id),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

        sw_obj.write(self.cursor, self.uid, sw_id.id, {"state": "pending"})

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            u"Cas ATC {} no es pot cancel·lar: R1 05 l'heu de revisar i tancar - Error manual R1 no oberta".format(  # noqa: E501
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

    def test__case_cancel_ATC_with_R108__NOCancelATC__via_import(self):
        """
        Test case_cancel for atc 'open' with R108, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r108_new.xml"
        )

        self.switch(self.txn, "comer")

        r101_obj = self.openerp.pool.get("giscedata.switching.r1.01")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-01
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "01")

        r101 = r101_obj.browse(self.cursor, self.uid, step_id)
        sw_obj.write(self.cursor, self.uid, r101.sw_id.id, {"codi_sollicitud": "201607211259"})
        # El creem ara perque la data sigui posterior a la posada al r101
        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        self.switch(self.txn, "distri")
        sw_obj.importar_xml(self.cursor, self.uid, r1_xml, "r108.xml")
        sw_id = sw_obj.browse(self.cursor, self.uid, r101.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 08 no pots cancel·lar una cancel·lació, cal esperar a rebre pas 09 de distribuïdora".format(  # noqa: E501
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

    def test__case_cancel_ATC_with_R108__NOCancelATC__via_create_case_and_step(self):
        """
        Test case_cancel for atc 'open' with R108, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        self.switch(self.txn, "comer")

        r108_obj = self.openerp.pool.get("giscedata.switching.r1.08")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-08
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "08")

        r108 = r108_obj.browse(self.cursor, self.uid, step_id)

        sw_id = sw_obj.browse(self.cursor, self.uid, r108.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 08 no pots cancel·lar una cancel·lació, cal esperar a rebre pas 09 de distribuïdora".format(  # noqa: E501
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

    def test__case_cancel_ATC_with_R109__no_rebuig__NOCancelATC(self):
        """
        Test case_cancel for atc 'open' with R109, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r109_new.xml"
        )

        self.switch(self.txn, "comer")

        r108_obj = self.openerp.pool.get("giscedata.switching.r1.08")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-08
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "08")

        r108 = r108_obj.browse(self.cursor, self.uid, step_id)

        sw_id = sw_obj.browse(self.cursor, self.uid, r108.sw_id.id)

        sw_obj.write(self.cursor, self.uid, sw_id.id, {"codi_sollicitud": "201607211259"})

        # El creem ara perque la data sigui posterior a la posada al r101
        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        sw_obj.importar_xml(self.cursor, self.uid, r1_xml, "r109.xml")

        sw_id = sw_obj.browse(self.cursor, self.uid, r108.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 09 d'acceptació s'ha de tancar i no cancel·lar".format(  # noqa: E501
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

    def test__case_cancel_ATC_with_R109__rebuig__NOCancelATC(self):
        """
        Test case_cancel for atc 'open' with R109, ATC is not cancelled
        """
        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r109_new.xml"
        )

        self.switch(self.txn, "comer")

        r108_obj = self.openerp.pool.get("giscedata.switching.r1.08")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        act_obj.write(
            self.cursor,
            self.uid,
            act_obj.search(self.cursor, self.uid, [], context={"active_test": False}),
            {"active": True, "is_automatic": True},
        )

        contract_id = self.get_contract_id(self.txn)
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        # Creates step R1-08
        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "08")

        r108 = r108_obj.browse(self.cursor, self.uid, step_id)

        sw_id = sw_obj.browse(self.cursor, self.uid, r108.sw_id.id)

        sw_obj.write(self.cursor, self.uid, sw_id.id, {"codi_sollicitud": "201607211259"})

        # El creem ara perque la data sigui posterior a la posada al r101
        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))
            r1_xml = r1_xml.replace(
                "MensajeAceptacionAnulacionReclamacion", "MensajeRechazoReclamacion"
            )
            r1_xml = r1_xml.replace("AceptacionAnulacion", "Rechazos")
            r1_xml = r1_xml.replace("FechaAceptacion", "FechaRechazo")
            dada_rebuig = """<Rechazo>
                            <Secuencial>1</Secuencial>
                            <CodigoMotivo>F1</CodigoMotivo>
                            <Comentarios>Motiu de rebuig F1</Comentarios>
                            </Rechazo>
                            <RegistrosDocumento>
                            <RegistroDoc>
                                <TipoDocAportado>08</TipoDocAportado>
                                <DireccionUrl>http://eneracme.com/docs/NIF11111111H.pdf</DireccionUrl>
                            </RegistroDoc>
                            <RegistroDoc>
                                <TipoDocAportado>07</TipoDocAportado>
                                <DireccionUrl>http://eneracme.com/docs/NIF11111111H.pdf</DireccionUrl>
                            </RegistroDoc>
                            </RegistrosDocumento>"""
            r1_xml = r1_xml.replace("</FechaRechazo>", "</FechaRechazo>" + dada_rebuig)

        sw_obj.importar_xml(self.cursor, self.uid, r1_xml, "r109.xml")

        sw_id = sw_obj.browse(self.cursor, self.uid, r108.sw_id.id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(
            self.cursor,
            self.uid,
            atc_id,
            {"state": "open", "ref": "giscedata.switching,{}".format(sw_id.id)},
        )

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: R1 09 de rebuig no es pot cancel·lar ni tancar".format(  # noqa: E501
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "open")

    def test__case_cancel_ATC_done__NOcancelATC(self):
        """
        Test case_cancel for atc 'done' ATC is cancelled
        """

        atc_o = self.pool.get("giscedata.atc")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]
        atc_o.write(self.cursor, self.uid, atc_id, {"state": "done"})

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception as e:
            atc_e = e

        self.assertEqual(
            atc_e.value,
            "Cas ATC {} no es pot cancel·lar: L'estat no és Pendent, Esborrany o Obert".format(
                atc_id
            ),
        )

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, "done")
