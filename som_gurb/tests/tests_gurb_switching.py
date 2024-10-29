# -*- coding: utf-8 -*-
from tests_gurb_base import TestsGurbBase
from addons import get_module_resource
from tools.misc import cache
import mock
from destral.patch import PatchNewCursors
from osv import osv


class GiscedataSwitching(osv.osv):

    _name = "giscedata.switching"
    _inherit = "giscedata.switching"

    def importar_xml(self, cursor, uid, data, fname, context=None):
        if not context:
            context = {}
        with PatchNewCursors():
            res = super(GiscedataSwitching, self).importar_xml(cursor, uid, data, fname, context)
        return res


GiscedataSwitching()


class TestsGurbSwitching(TestsGurbBase):

    def get_contract_id(self, txn, xml_id="polissa_0001"):
        uid = txn.user
        cursor = txn.cursor
        imd_obj = self.openerp.pool.get("ir.model.data")

        return imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", xml_id
        )[1]

    @mock.patch("giscedata_switching.giscedata_switching.GiscedataSwitching.whereiam")
    def switch(
        self,
        txn,
        where,
        mock_function,
        is_autocons=False,
        other_id_name="res_partner_agrolait",
        context=None,
    ):
        if context is None:
            context = {}
        cursor = txn.cursor
        uid = txn.user
        mock_function.return_value = where
        imd_obj = self.openerp.pool.get("ir.model.data")
        partner_obj = self.openerp.pool.get("res.partner")
        cups_obj = self.openerp.pool.get("giscedata.cups.ps")
        partner_id = imd_obj.get_object_reference(
            cursor, uid, "base", "main_partner"
        )[1]
        other_id = imd_obj.get_object_reference(
            cursor, uid, "base", other_id_name
        )[1]
        another_id = imd_obj.get_object_reference(
            cursor, uid, "base", "res_partner_c2c"
        )[1]

        if is_autocons:
            codes = {"distri": "4321", "comer": "1234"}
        else:
            codes = {"distri": "1234", "comer": "4321"}

        partner_obj.write(cursor, uid, [partner_id], {
            "ref": codes.pop(where)
        })
        partner_obj.write(cursor, uid, [other_id], {
            "ref": codes.values()[0]
        })
        partner_obj.write(cursor, uid, [another_id], {
            "ref": "5555"
        })
        cups_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_cups", context.get("cups_xml_id", "cups_01")
        )[1]
        distri_ids = {"distri": partner_id, "comer": other_id}
        cups_obj.write(cursor, uid, [cups_id], {
            "distribuidora_id": distri_ids[where]
        })
        pol_o = self.openerp.pool.get("giscedata.polissa")
        pol_id = pol_o.search(cursor, uid, [("cups", "=", cups_id)])
        if where == "distri":
            pol_o.write(
                cursor, uid, pol_id, {"comercialitzadora": other_id, "distribuidora": partner_id}
            )
        if context.get("another_comer_id"):
            pol_o.write(
                cursor, uid, pol_id, {"comercialitzadora": another_id, "distribuidora": partner_id}
            )
        cache.clean_caches_for_db(cursor.dbname)

    def update_polissa_distri(self, txn, pol_ref="polissa_0001"):
        """
        Sets the distribuidora_id field in contract as the same of related cups
        """
        cursor = txn.cursor
        uid = txn.user
        imd_obj = self.openerp.pool.get("ir.model.data")

        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cups_obj = self.openerp.pool.get("giscedata.cups.ps")

        contract_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", pol_ref
        )[1]
        cups_id = pol_obj.read(cursor, uid, contract_id, ["cups"])["cups"][0]
        distri_id = cups_obj.read(
            cursor, uid, cups_id, ["distribuidora_id"]
        )["distribuidora_id"][0]
        pol_obj.write(cursor, uid, contract_id, {"distribuidora": distri_id})

    def change_polissa_comer(self, txn, pol_id="polissa_0001"):
        cursor = txn.cursor
        uid = txn.user
        imd_obj = self.openerp.pool.get("ir.model.data")
        new_comer_id = imd_obj.get_object_reference(
            cursor, uid, "base", "res_partner_c2c"
        )[1]
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        pol_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", pol_id
        )[1]
        pol_obj.write(cursor, uid, [pol_id], {
            "comercialitzadora": new_comer_id
        })

    def create_case_and_step(
            self, cursor, uid, contract_id, proces_name, step_name, sw_id_origin=None, context=None
    ):
        """
        Creates case and step
        :param proces_name:
        :param step_name:
        :param context:
        :return:
        """
        if context is None:
            context = {}
        context["proces_name"] = proces_name
        if isinstance(sw_id_origin, dict):
            context = sw_id_origin
            sw_id_origin = None

        sw_obj = self.openerp.pool.get("giscedata.switching")

        swproc_obj = self.openerp.pool.get("giscedata.switching.proces")
        swpas_obj = self.openerp.pool.get("giscedata.switching.step")
        swinfo_obj = self.openerp.pool.get(
            "giscedata.switching.step.info"
        )
        contract_obj = self.openerp.pool.get("giscedata.polissa")

        proces_id = swproc_obj.search(
            cursor, uid, [("name", "=", proces_name)]
        )[0]

        sw_params = {
            "proces_id": proces_id,
            "cups_polissa_id": contract_id,
        }

        vals = sw_obj.onchange_polissa_id(
            cursor, uid, [], contract_id, None, context=context
        )

        sw_params.update(vals["value"])

        if not sw_params.get("ref_contracte", False):
            sw_params["ref_contracte"] = "111111111"

        old_val = None
        if sw_id_origin:
            sw_id = sw_id_origin
        else:
            sw_id = sw_obj.create(cursor, uid, sw_params)
            if context.get("whereiam"):
                old_val = sw_obj.read(cursor, uid, sw_id, ["whereiam"])["whereiam"]
                cursor.execute(
                    "UPDATE giscedata_switching SET whereiam = %s WHERE id = %s",
                    (context.get("whereiam"), sw_id)
                )

        if proces_name in ["C1", "C2", "E1", "T1"]:
            out_retail = contract_obj.read(
                cursor, uid, contract_id, ["comercialitzadora"]
            )["comercialitzadora"][0]
            sw_obj.write(cursor, uid, sw_id, {"comer_sortint_id": out_retail})

        # Create step
        pas_id = swpas_obj.get_step(cursor, uid, step_name, proces_name)

        # Create step info
        info_vals = {
            "sw_id": sw_id,
            "proces_id": proces_id,
            "step_id": pas_id,
        }
        old_val = None
        if context.get("whereiam"):
            old_val = sw_obj.read(cursor, uid, sw_id, ["whereiam"])["whereiam"]
            cursor.execute(
                "UPDATE giscedata_switching SET whereiam = %s WHERE id = %s",
                (context.get("whereiam"), sw_id)
            )
        info_id = swinfo_obj.create(cursor, uid, info_vals, context=context)
        if context.get("whereiam"):
            cursor.execute(
                "UPDATE giscedata_switching SET whereiam = %s WHERE id = %s",
                (old_val, sw_id)
            )
        info = swinfo_obj.browse(cursor, uid, info_id)
        model_obj, model_id = info.pas_id.split(",")
        if old_val:
            cursor.execute(
                "UPDATE giscedata_switching SET whereiam = %s WHERE id = %s",
                (old_val, sw_id)
            )
        return int(model_id)

    def set_autoconsumo(self, txn, autoconsumo_mode="00"):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get("ir.model.data")

        cursor = txn.cursor
        uid = txn.user

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0001"
        )[1]
        polissa_obj.write(cursor, uid, [polissa_id], {
            "autoconsumo": autoconsumo_mode,
        })

    def test_do_not_notify_m1_02_auto_gurb_category(self):
        """
        Test that M102"s are not notified when:
            - Is a self-consumption change
            - Contract has GURB category
        """
        m1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new.xml"
        )
        with open(m1_xml_path, "r") as f:
            m1_xml = f.read()

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn)

        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_0001"})

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")
        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        sw_obj = self.openerp.pool.get("giscedata.switching")
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "S"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud
        m1_xml = m1_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )

        # Import XML
        sw_obj.importar_xml(self.cursor, self.uid, m1_xml, "m102.xml")

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "02"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "02")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "open")
        self.assertEqual(m1.notificacio_pendent, False)

    def test_notify_m1_02_auto_no_gurb_category(self):
        """
        Test that self-consumption M102"s are notified when contract does not have GURB category
        """
        m1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new.xml"
        )
        with open(m1_xml_path, "r") as f:
            m1_xml = f.read()

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn)

        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(set_gurb_category=False, context={
                                  "polissa_xml_id": "polissa_0001"})

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")
        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        sw_obj = self.openerp.pool.get("giscedata.switching")
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "S"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud
        m1_xml = m1_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )

        # Import XML
        sw_obj.importar_xml(self.cursor, self.uid, m1_xml, "m102.xml")

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "02"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "02")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "open")
        self.assertEqual(m1.notificacio_pendent, True)

    def test_notify_m1_02_no_auto_gurb_category(self):
        """
        Test that no self-consumption M102"s are notified when contract has GURB category
        """
        m1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new.xml"
        )
        with open(m1_xml_path, "r") as f:
            m1_xml = f.read()

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn)

        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_0001"})

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")
        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        sw_obj = self.openerp.pool.get("giscedata.switching")
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "N"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud
        m1_xml = m1_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )

        # Import XML
        sw_obj.importar_xml(self.cursor, self.uid, m1_xml, "m102.xml")

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "02"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "02")
        self.assertEqual(m101.solicitud_autoconsum, "N")

        self.assertEqual(m1.state, "open")
        self.assertEqual(m1.notificacio_pendent, True)

    def test_close_m1_02_unidirectional_auto_gurb_category(self):
        """
        Test that unidirectional self-consumption M1"s are closed when contract has GURB category
        """
        m1_02_rej_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new_rej.xml"
        )
        with open(m1_02_rej_xml_path, "r") as f:
            m1_02_rej_xml = f.read()

        sw_obj = self.openerp.pool.get("giscedata.switching")

        self.switch(self.txn, "comer")
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_0001"})

        # Import XML
        sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_rej_xml, "invalid_canvi.xml"
        )

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "02"),
            ("codi_sollicitud", "=", "202307177214")
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.rebuig, True)
        inf = u"REBUIG UNIDIRECCIONAL AUTO.  Rebuig: El CAU indicado en los " \
            u"ficheros no existe en SF.No se encuentra ningún Fichero de " \
            u"Coeficientes de Reparto."
        self.assertEqual(inf, m1.additional_info)

        self.assertEqual(m1.state, "cancel")
        self.assertEqual(m1.notificacio_pendent, False)

    def test_close_m1_02_rej_auto_gurb_category(self):
        """
        Test that rejection self-consumption M1"s are closed when contract has GURB category
        """
        m1_02_rej_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new_rej.xml"
        )
        with open(m1_02_rej_xml_path, "r") as f:
            m1_02_rej_xml = f.read()

        sw_obj = self.openerp.pool.get("giscedata.switching")

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn)

        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_0001"})

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")
        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        sw_obj = self.openerp.pool.get("giscedata.switching")
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "S"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud
        m1_02_rej_xml = m1_02_rej_xml.replace(
            "<CodigoDeSolicitud>202307177214",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )

        # Import XML
        sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_rej_xml, "invalid_canvi.xml"
        )

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "02"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "02")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "cancel")
        self.assertEqual(m1.notificacio_pendent, False)

    def test_do_not_close_m1_02_rej_auto_no_gurb_category(self):
        """
        Test that rejection self-consumption M1"s are not closed when
        contract does not have GURB category
        """
        m1_02_rej_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new_rej.xml"
        )
        with open(m1_02_rej_xml_path, "r") as f:
            m1_02_rej_xml = f.read()

        sw_obj = self.openerp.pool.get("giscedata.switching")

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn)

        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(set_gurb_category=False, context={
                                  "polissa_xml_id": "polissa_0001"})

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")
        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        sw_obj = self.openerp.pool.get("giscedata.switching")
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "S"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud
        m1_02_rej_xml = m1_02_rej_xml.replace(
            "<CodigoDeSolicitud>202307177214",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )

        # Import XML
        sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_rej_xml, "invalid_canvi.xml"
        )

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "02"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "02")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "open")
        self.assertEqual(m1.notificacio_pendent, True)

    def test_close_d1_01_gurb_category(self):
        d1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "d101_new.xml"
        )
        with open(d1_xml_path, "r") as f:
            d1_xml = f.read()

        sw_obj = self.openerp.pool.get("giscedata.switching")
        self.switch(self.txn, "comer")
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_0001"})
        sw_obj.importar_xml(
            self.cursor, self.uid, d1_xml, "d101.xml"
        )

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "D1"),
            ("step_id.name", "=", "01"),
            ("codi_sollicitud", "=", "201608120830"),
        ])
        self.assertEqual(len(res), 1)

        d1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(d1.proces_id.name, "D1")
        self.assertEqual(d1.step_id.name, "01")
        self.assertEqual(d1.state, "done")
        self.assertEqual(d1.notificacio_pendent, False)

    @mock.patch('poweremail.poweremail_template.poweremail_templates.generate_mail')
    @mock.patch(
        'giscedata_switching.giscedata_switching.GiscedataSwitchingActivacionsConfig.get_activation_method'  # noqa: F821, E501
    )
    def test_do_close_m1_05_gurb_category(self, get_activation_method, generate_mail):
        """
        Test that self-consumption M1"s are closed when
        contract does have GURB category
        """
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        sw_obj = self.openerp.pool.get("giscedata.switching")
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")

        generate_mail.return_value = True
        get_activation_method.return_value = ['activar_polissa_from_m1']

        m1_02_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new.xml"
        )
        with open(m1_02_xml_path, "r") as f:
            m1_02_xml = f.read()

        m1_05_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m105_canvi_autoconsum.xml"
        )
        with open(m1_05_xml_path, "r") as f:
            m1_05_xml = f.read()

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")

        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        self.update_polissa_distri(self.txn, pol_ref='polissa_tarifa_018')
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_tarifa_018"})
        pol = pol_obj.browse(self.cursor, self.uid, contract_id)
        cups = pol.cups.name

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )
        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "S"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud
        m1_02_xml = m1_02_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_02_xml = m1_02_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups)
        )

        m1_05_xml = m1_05_xml.replace(
            "<CodigoDeSolicitud>201607211260",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_05_xml = m1_05_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups)
        )

        # Import XML
        sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_xml, "m1_02.xml"
        )

        sw_obj.importar_xml(
            self.cursor, self.uid, m1_05_xml, "m1_05.xml"
        )

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "05"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "05")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "done")
        self.assertEqual(m1.notificacio_pendent, False)

    def test_notify_m1_03_gurb_category(self):
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        sw_obj = self.openerp.pool.get("giscedata.switching")
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")

        m1_02_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new.xml"
        )
        with open(m1_02_xml_path, "r") as f:
            m1_02_xml = f.read()

        m1_03_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m103_new.xml"
        )
        with open(m1_03_xml_path, "r") as f:
            m1_03_xml = f.read()

        sw_obj = self.openerp.pool.get("giscedata.switching")

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")

        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        self.update_polissa_distri(self.txn, pol_ref='polissa_tarifa_018')
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_tarifa_018"})
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups.name

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )

        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "S"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud

        m1_02_xml = m1_02_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_02_xml = m1_02_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups)
        )

        m1_03_xml = m1_03_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_03_xml = m1_03_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups)
        )

        # Import XML
        sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_xml, "m1_02.xml"
        )

        sw_obj.importar_xml(
            self.cursor, self.uid, m1_03_xml, "m1_03.xml"
        )

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "03"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "03")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "cancel")
        self.assertEqual(m1.notificacio_pendent, False)

    def test_notify_m1_04_gurb_category(self):
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        sw_obj = self.openerp.pool.get("giscedata.switching")
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")
        m1_02_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m102_new.xml"
        )
        with open(m1_02_xml_path, "r") as f:
            m1_02_xml = f.read()

        m1_04_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m104_new.xml"
        )
        with open(m1_04_xml_path, "r") as f:
            m1_04_xml = f.read()

        self.switch(self.txn, "comer")

        # Create M1 01
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')

        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        self.update_polissa_distri(self.txn, pol_ref='polissa_tarifa_018')
        self.activar_polissa_CUPS(set_gurb_category=True, context={
                                  "polissa_xml_id": "polissa_tarifa_018"})
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups.name

        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "M1", "01"
        )
        sw_step_header_id = step_obj.read(
            self.cursor, self.uid, step_id, ["header_id"]
        )["header_id"][0]
        sw_step_header_obj.write(
            self.cursor, self.uid, sw_step_header_id, {"notificacio_pendent": False}
        )
        m101 = step_obj.browse(self.cursor, self.uid, step_id)

        # Set self-consumption modification
        step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "S"})

        # Change "CodigoDeSolicitud" in XML
        m1 = sw_obj.browse(self.cursor, self.uid, m101.sw_id.id)
        codi_sollicitud = m1.codi_sollicitud
        m1_02_xml = m1_02_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_02_xml = m1_02_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups)
        )

        m1_04_xml = m1_04_xml.replace(
            "<CodigoDeSolicitud>123456789123",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_04_xml = m1_04_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups)
        )

        # Import XML
        sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_xml, "m1_02.xml"
        )

        sw_obj.importar_xml(
            self.cursor, self.uid, m1_04_xml, "m1_04.xml"
        )

        res = sw_obj.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "04"),
            ("codi_sollicitud", "=", codi_sollicitud)
        ])
        self.assertEqual(len(res), 1)

        m1 = sw_obj.browse(self.cursor, self.uid, res[0])
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "04")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "cancel")
        self.assertEqual(m1.notificacio_pendent, False)
