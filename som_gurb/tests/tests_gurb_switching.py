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
            "tipus_subseccio": autoconsumo_mode,
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

        sgc_obj = self.openerp.pool.get("som.gurb.cups")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

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
        sgc_obj = self.openerp.pool.get("som.gurb.cups")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

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
        sgc_obj = self.openerp.pool.get("som.gurb.cups")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

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
                                  "polissa_xml_id": "polissa_tarifa_019"})

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
        sgc_obj = self.openerp.pool.get("som.gurb.cups")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

        self.switch(self.txn, "comer")
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_0001"})
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
        sgc_obj = self.openerp.pool.get("som.gurb.cups")
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

        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups

        gurb_cups_0002_id = sgc_obj.search(
            self.cursor, self.uid, [('cups_id', '=', cups.id)]
        )[0]
        gurb_cups_0002 = sgc_obj.browse(self.cursor, self.uid, gurb_cups_0002_id)
        gurb_cups_0002.send_signal('button_create_cups')
        gurb_cups_0002.send_signal('button_activate_cups')

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
            "<CUPS>{0}".format(cups.name)
        )

        m1_05_xml = m1_05_xml.replace(
            "<CodigoDeSolicitud>201607211260",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_05_xml = m1_05_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
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
        pol = pol_obj.browse(self.cursor, self.uid, contract_id)
        self.assertEqual(m1.proces_id.name, "M1")
        self.assertEqual(m1.step_id.name, "05")
        self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "done")
        self.assertEqual(m1.notificacio_pendent, False)

        self.assertEqual(pol.tipus_subseccio, "00")

        gurb_cups_id = sgc_obj.search(
            self.cursor, self.uid, [('cups_id', '=', m1.cups_polissa_id.cups.id)]
        )[0]
        gurb_cups = sgc_obj.browse(self.cursor, self.uid, gurb_cups_id)
        self.assertEqual(gurb_cups.state, 'active')

    def test_notify_m1_03_gurb_category(self):
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        sw_obj = self.openerp.pool.get("giscedata.switching")
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.openerp.pool.get("giscedata.switching.step.header")
        sgc_obj = self.openerp.pool.get("som.gurb.cups")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

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
        sgc_obj = self.openerp.pool.get("som.gurb.cups")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

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

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_c1_06_cancel_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get('giscedata.switching')
        sgc_obj = self.openerp.pool.get('som.gurb.cups')
        self.openerp.pool.get('giscedata.switching.step.header')
        self.openerp.pool.get('giscedata.switching.c1.06')
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_gurb', 'gurb_cups_0002')[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal('button_create_cups')
        sgc_0002.send_signal('button_activate_cups')

        c1_06_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "c106_new.xml"
        )
        with open(c1_06_xml_path, "r") as f:
            c1_06_xml = f.read()

        self.switch(self.txn, "comer")
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups

        # Change "CodigoDeSolicitud" in XML
        c1_06_xml = c1_06_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, c1_06_xml, "c1_06.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, 'comming_cancellation')

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_c2_06_cancel_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get('giscedata.switching')
        sgc_obj = self.openerp.pool.get('som.gurb.cups')
        self.openerp.pool.get('giscedata.switching.step.header')
        self.openerp.pool.get('giscedata.switching.c1.06')
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_gurb', 'gurb_cups_0002')[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal('button_create_cups')
        sgc_0002.send_signal('button_activate_cups')

        c2_06_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "c206_new.xml"
        )
        with open(c2_06_xml_path, "r") as f:
            c2_06_xml = f.read()

        self.switch(self.txn, "comer")
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups

        # Change "CodigoDeSolicitud" in XML
        c2_06_xml = c2_06_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, c2_06_xml, "c2_06.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, 'comming_cancellation')

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_m1_01_subrogacio_atr_pending_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        self.openerp.pool.get('giscedata.switching')
        sgc_obj = self.openerp.pool.get('som.gurb.cups')
        self.openerp.pool.get("giscedata.polissa")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_gurb', 'gurb_cups_0002')[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal('button_create_cups')
        sgc_0002.send_signal('button_activate_cups')

        # Creem el M1 01sw_obj
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')
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
        step_obj.write(self.cursor, self.uid, step_id, {"sollicitudadm": "S"})
        step_obj.write(self.cursor, self.uid, step_id, {"canvi_titular": "S"})

        m101 = step_obj.browse(self.cursor, self.uid, step_id)
        step_obj.generar_xml(self.cursor, self.uid, m101.id)
        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, 'atr_pending')

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_m1_02_subrogacio_cancel_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get('giscedata.switching')
        sgc_obj = self.openerp.pool.get('som.gurb.cups')
        m101_obj = self.openerp.pool.get('giscedata.switching.m1.01')
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_gurb', 'gurb_cups_0002')[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal('button_create_cups')
        sgc_0002.send_signal('button_activate_cups')

        # Creem el M1 01
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')
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
        step_obj.write(self.cursor, self.uid, step_id, {"sollicitudadm": "S"})
        step_obj.write(self.cursor, self.uid, step_id, {"canvi_titular": "S"})
        m101 = step_obj.browse(self.cursor, self.uid, step_id)
        codi_sollicitud = m101.sw_id.codi_sollicitud
        m101_obj.generar_xml(self.cursor, self.uid, step_id)

        # Carreguem el M102
        m1_02_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m102_ss_new.xml"
        )
        with open(m1_02_xml_path, "r") as f:
            m1_02_xml = f.read()

        self.switch(self.txn, "comer")

        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups

        # Change "CodigoDeSolicitud" in XML
        m1_02_xml = m1_02_xml.replace(
            "<CodigoDeSolicitud>201412111009",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_02_xml = m1_02_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_xml, "m102_ss_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, 'comming_cancellation')

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_m1_05_traspas_cancel_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get('giscedata.switching')
        sgc_obj = self.openerp.pool.get('som.gurb.cups')
        m101_obj = self.openerp.pool.get('giscedata.switching.m1.01')
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_gurb', 'gurb_cups_0002')[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal('button_create_cups')
        sgc_0002.send_signal('button_activate_cups')

        # Creem el M1 01
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')
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
        step_obj.write(self.cursor, self.uid, step_id, {"sollicitudadm": "S"})
        step_obj.write(self.cursor, self.uid, step_id, {"canvi_titular": "T"})

        m101 = step_obj.browse(self.cursor, self.uid, step_id)
        codi_sollicitud = m101.sw_id.codi_sollicitud
        m101_obj.generar_xml(self.cursor, self.uid, step_id)

        # Carreguem el M102
        m1_02_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m102_st_new.xml"
        )
        with open(m1_02_xml_path, "r") as f:
            m1_02_xml = f.read()
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups
        # Change "CodigoDeSolicitud" in XML
        m1_02_xml = m1_02_xml.replace(
            "<CodigoDeSolicitud>202412161862",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_02_xml = m1_02_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_xml, "m102_st_new.xml"
        )

        # Import XML M105
        m1_05_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m105_st_new.xml"
        )
        with open(m1_05_xml_path, "r") as f:
            m1_05_xml = f.read()
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups
        # Change "CodigoDeSolicitud" in XML
        m1_05_xml = m1_05_xml.replace(
            "<CodigoDeSolicitud>202412161862",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_05_xml = m1_05_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m1_05_xml, "m105_st_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, 'comming_cancellation')

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_m1_01_traspas_atr_pending_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        self.openerp.pool.get('giscedata.switching')
        sgc_obj = self.openerp.pool.get('som.gurb.cups')
        self.openerp.pool.get('giscedata.switching.step.header')
        self.openerp.pool.get('giscedata.switching.m1.02')
        self.openerp.pool.get("giscedata.polissa")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_gurb', 'gurb_cups_0002')[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal('button_create_cups')
        sgc_0002.send_signal('button_activate_cups')

        # Creem el M1 01
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')
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
        step_obj.write(self.cursor, self.uid, step_id, {"sollicitudadm": "S"})
        step_obj.write(self.cursor, self.uid, step_id, {"canvi_titular": "T"})

        m101 = step_obj.browse(self.cursor, self.uid, step_id)
        step_obj.generar_xml(self.cursor, self.uid, m101.id)

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, 'atr_pending')

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_m1_02_traspas_rebuig(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get('giscedata.switching')
        sgc_obj = self.openerp.pool.get('som.gurb.cups')
        m101_obj = self.openerp.pool.get('giscedata.switching.m1.01')
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_gurb', 'gurb_cups_0002')[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal('button_create_cups')
        sgc_0002.send_signal('button_activate_cups')

        # Creem el M1 01
        contract_id = self.get_contract_id(self.txn, xml_id='polissa_tarifa_018')
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
        step_obj.write(self.cursor, self.uid, step_id, {"sollicitudadm": "S"})
        step_obj.write(self.cursor, self.uid, step_id, {"canvi_titular": "T"})

        m101 = step_obj.browse(self.cursor, self.uid, step_id)
        codi_sollicitud = m101.sw_id.codi_sollicitud
        m101_obj.generar_xml(self.cursor, self.uid, step_id)

        # Carreguem el M102
        m1_02_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m102_st_new_rej.xml"
        )
        with open(m1_02_xml_path, "r") as f:
            m1_02_xml = f.read()
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups
        # Change "CodigoDeSolicitud" in XML
        m1_02_xml = m1_02_xml.replace(
            "<CodigoDeSolicitud>202412161862",
            "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
        )
        m1_02_xml = m1_02_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_xml, "m102_st_new_rej.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, 'active')

    @mock.patch('som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change')
    def test_create_from_xml_m2_05_unexpected_leaving_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get("giscedata.switching")
        sgc_obj = self.openerp.pool.get("som.gurb.cups")
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        contract_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

        # Import XML M2_05
        m2_05_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m205_new.xml"
        )
        with open(m2_05_xml_path, "r") as f:
            m2_05_xml = f.read()
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups

        m2_05_xml = m2_05_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )
        m2_05_xml = m2_05_xml.replace(
            "<Motivo>01",
            "<Motivo>{0}".format("06")
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m2_05_xml, "m205_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, "atr_pending")

    @mock.patch("som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change")
    def test_create_from_xml_m2_05_expected_leaving_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get("giscedata.switching")
        sgc_obj = self.openerp.pool.get("som.gurb.cups")
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        contract_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")
        sgc_0002.send_signal("button_coming_cancellation")

        # Import XML M2_05
        m2_05_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m205_new.xml"
        )
        with open(m2_05_xml_path, "r") as f:
            m2_05_xml = f.read()
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups

        m2_05_xml = m2_05_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )
        m2_05_xml = m2_05_xml.replace(
            "<Motivo>01",
            "<Motivo>{0}".format("06")
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m2_05_xml, "m205_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        self.assertEqual(sgc_0002.state, "cancel")

    @mock.patch("som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change")
    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def test_create_from_xml_m2_05_activating_gurb(
            self, mock_send_gurb_activation_email, mock_is_unidirectional):
        mock_send_gurb_activation_email.return_value = False
        mock_is_unidirectional.return_value = False

        sw_obj = self.openerp.pool.get("giscedata.switching")
        sgc_obj = self.openerp.pool.get("som.gurb.cups")
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        contract_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")

        # Preparar el sgc_obj
        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")

        # Import XML M2_05
        m2_05_xml_path = get_module_resource(
            "som_gurb", "tests", "fixtures", "m205_new.xml"
        )
        with open(m2_05_xml_path, "r") as f:
            m2_05_xml = f.read()
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn, pol_id='polissa_tarifa_018')
        cups = pol_obj.browse(self.cursor, self.uid, contract_id).cups

        m2_05_xml = m2_05_xml.replace(
            "<CUPS>ES1234000000000001JN0F",
            "<CUPS>{0}".format(cups.name)
        )
        m2_05_xml = m2_05_xml.replace(
            "<Motivo>01",
            "<Motivo>{0}".format("04")
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m2_05_xml, "m205_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        self.assertEqual(sgc_0002.state, "active")

    def test_wizard_atr_gurb_model(self):
        wiz_o = self.openerp.pool.get("wizard.atr.gurb.model")
        context = {"active_ids": [1]}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)
        expected = {
            'domain': [('cups_polissa_id', 'in', [1, 19])],
            'name': 'Tots els casos ATR del GURB',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'giscedata.switching',
            'type': 'ir.actions.act_window',
            'view_id': False
        }
        res = wiz_o.list_all_pols(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(res, expected)
