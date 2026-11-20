# -*- coding: utf-8 -*-
from __future__ import absolute_import

from copy import deepcopy
from lxml import etree

from .tests_gurb_base import TestsGurbBase
from addons import get_module_resource
from tools.misc import cache
import mock
from base_extended_som.tests.utils import avoid_creating_subcursors
from osv import osv


class GiscedataSwitching(osv.osv):

    _name = "giscedata.switching"
    _inherit = "giscedata.switching"

    def importar_xml(self, cursor, uid, data, fname, context=None):
        if not context:
            context = {}
        with avoid_creating_subcursors(cursor):
            res = super(GiscedataSwitching, self).importar_xml(cursor, uid, data, fname, context)
        return res


GiscedataSwitching()


class TestsGurbSwitching(TestsGurbBase):

    _config_step_validation_fnc = (
        "giscedata_switching.giscedata_switching_a3."
        "GiscedataSwitchingA3_01.config_step_validation"
    )

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
            "ref": list(codes.values())[0]
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

    def _config_m101_autoconsum(self, m101, config_step_validation_mock=None):
        imd_obj = self.openerp.pool.get('ir.model.data')
        generador_obj = self.openerp.pool.get('giscedata.autoconsum.generador')
        partner_address_obj = self.openerp.pool.get('res.partner.address')
        dades_cau_obj = self.openerp.pool.get('giscedata.switching.datos.cau')
        autoconsum_obj = self.openerp.pool.get('giscedata.autoconsum')

        partner_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'base', 'res_partner_gisce')[1]
        hist_autoconsum_id = imd_obj.get_object_reference(
            self.cursor, self.uid,
            'giscedata_cups', 'rel_autoconsum_cups_tarifa_018_autoconsum_41')[1]
        autoconsum_id = imd_obj.get_object_reference(
            self.cursor, self.uid,
            'giscedata_cups', 'autoconsum_cups_tarifa_018_autoconsum_41')[1]
        generador_id = imd_obj.get_object_reference(
            self.cursor, self.uid,
            'giscedata_cups', 'generador_autoconsum_cups_tarifa_018_autoconsum_41')[1]

        if config_step_validation_mock is not None:
            config_step_validation_mock.return_value = True

        autoconsum_obj.send_signal(self.cursor, self.uid, [autoconsum_id], ['validar', 'crear'])
        partner_generador_id = generador_obj.read(
            self.cursor, self.uid, generador_id, ['partner_id'])['partner_id'][0]
        partner_address_obj.create(self.cursor, self.uid, {
            'phone': 666999222, 'partner_id': partner_generador_id})
        dades_cau_ids = dades_cau_obj.crear_datos_cau_sense_sw(
            self.cursor, self.uid, hist_autoconsum_id, "modificar")
        vals = {
            'dades_cau': dades_cau_ids,
            'change_type': 'tarpot',
            'tariff': '018',
            'contact': partner_id,
            'phone_num': '666888555',
            'phone_pre': '034',
            'con_name': '0018_A41',
            'con_sur1': 'asdfg',
            'con_sur2': 'gfdsa',
            'power_p1': 4600,
            'power_p2': 4600,
            'power_p3': 4600,
            'power_invoicing': '1',
        }
        m101.config_step(vals)

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

    @mock.patch(_config_step_validation_fnc)
    def test_do_not_notify_m1_02_auto_gurb_category(self, config_step_validation_mock):
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
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_0001"})

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

        self._config_m101_autoconsum(m101, config_step_validation_mock)

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

        self.assertEqual(m1.state, "open")
        self.assertEqual(m1.notificacio_pendent, False)

    @mock.patch(_config_step_validation_fnc)
    def test_notify_m1_02_auto_no_gurb_category(self, config_step_validation_mock):
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
        self.activar_polissa_CUPS(
            set_gurb_category=False, context={"polissa_xml_id": "polissa_0001"})

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

        self._config_m101_autoconsum(m101, config_step_validation_mock)

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
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_0001"})

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
        # step_obj.write(self.cursor, self.uid, step_id, {"solicitud_autoconsum": "N"})

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
        # self.assertEqual(m101.solicitud_autoconsum, "N")

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
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_0001"})

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

    @mock.patch(_config_step_validation_fnc)
    def test_close_m1_02_rej_auto_gurb_category(self, config_step_validation_mock):
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
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_0001"})

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

        self._config_m101_autoconsum(m101, config_step_validation_mock)

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

        self.assertEqual(m1.state, "cancel")
        self.assertEqual(m1.notificacio_pendent, False)

    @mock.patch(_config_step_validation_fnc)
    def test_do_not_close_m1_02_rej_auto_no_gurb_category(self, config_step_validation_mock):
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
        self.activar_polissa_CUPS(
            set_gurb_category=False, context={"polissa_xml_id": "polissa_tarifa_019"})

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

        self._config_m101_autoconsum(m101, config_step_validation_mock)

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
        self.assertEqual(sgc_0002.state, "atr_pending")

    def test_do_close_m1_05_gurb_category(self):
        self._check_do_close_m1_05_gurb_category()

    def test_do_close_m1_05_gurb_pending_modification(self):
        self._check_do_close_m1_05_gurb_category(pending_modification=True)

    @mock.patch(_config_step_validation_fnc)
    @mock.patch('poweremail.poweremail_template.poweremail_templates.generate_mail')
    @mock.patch(
        'giscedata_switching.giscedata_switching.GiscedataSwitchingActivacionsConfig.get_activation_method'  # noqa: F821, E501
    )
    def _check_do_close_m1_05_gurb_category(
            self, get_activation_method, generate_mail, config_step_validation_mock,
            pending_modification=False):
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
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_tarifa_018"})

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

        self._config_m101_autoconsum(m101, config_step_validation_mock)

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
            "<CUPS>ES0021126262693495FV",
            "<CUPS>{0}".format(cups.name)
        )

        # Import XML
        sw_obj.importar_xml(
            self.cursor, self.uid, m1_02_xml, "m1_02.xml"
        )

        if pending_modification:
            gurb_cups_0002.send_signal('button_pending_modification')
            self.assertEqual(gurb_cups_0002.state, 'comming_modification')

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
        # self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "done")
        self.assertEqual(m1.notificacio_pendent, False)

        self.assertEqual(pol.tipus_subseccio, "00")

        gurb_cups_id = sgc_obj.search(
            self.cursor, self.uid, [('cups_id', '=', m1.cups_polissa_id.cups.id)]
        )[0]
        gurb_cups = sgc_obj.browse(self.cursor, self.uid, gurb_cups_id)
        self.assertEqual(gurb_cups.state, 'active')

    @mock.patch(_config_step_validation_fnc)
    def test_notify_m1_03_gurb_category(self, config_step_validation_mock):
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
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_tarifa_018"})
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

        self._config_m101_autoconsum(m101, config_step_validation_mock)

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
        # self.assertEqual(m101.solicitud_autoconsum, "S")

        self.assertEqual(m1.state, "cancel")
        self.assertEqual(m1.notificacio_pendent, False)

    @mock.patch(_config_step_validation_fnc)
    def test_notify_m1_04_gurb_category(self, config_step_validation_mock):
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
        self.activar_polissa_CUPS(
            set_gurb_category=True, context={"polissa_xml_id": "polissa_tarifa_018"})
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

        self._config_m101_autoconsum(m101, config_step_validation_mock)

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
        # self.assertEqual(m101.solicitud_autoconsum, "S")

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
        gurb_cau = "ES0026233884282635YDA000"

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
        m2_05_xml = m2_05_xml.replace(
            "<CAU>ES1234000000000001JN0FA001",
            "<CAU>{0}".format(gurb_cau)
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m2_05_xml, "m205_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        scb = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        self.assertEqual(scb.state, "atr_pending")
        beta = self.openerp.pool.get("som.gurb.cups.beta").browse(
            self.cursor, self.uid, self.get_references()["gurb_cups_beta_2_id"]
        )
        self.assertTrue(beta.active)
        self.assertFalse(beta.end_date)

    @mock.patch("som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change")
    def test_create_from_xml_m2_05_expected_leaving_gurb(
            self, mock_is_unidirectional):
        mock_is_unidirectional.return_value = False
        gurb_cau = "ES0026233884282635YDA000"

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
        m2_05_xml = m2_05_xml.replace(
            "<CAU>ES1234000000000001JN0FA001",
            "<CAU>{0}".format(gurb_cau)
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m2_05_xml, "m205_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        self.assertEqual(sgc_0002.state, "cancel")
        self.assertFalse(sgc_0002.active)
        self.assertEqual(sgc_0002.end_date, "2016-06-06")
        beta = self.openerp.pool.get("som.gurb.cups.beta").browse(
            self.cursor, self.uid, self.get_references()["gurb_cups_beta_2_id"]
        )
        self.assertFalse(beta.active)
        self.assertEqual(beta.end_date, "2016-06-06")

    @mock.patch("som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change")
    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def test_create_from_xml_m2_05_activating_gurb(
            self, mock_send_gurb_activation_email, mock_is_unidirectional):
        mock_send_gurb_activation_email.return_value = False
        mock_is_unidirectional.return_value = False
        gurb_cau = "ES0026233884282635YDA000"

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
        m2_05_xml = m2_05_xml.replace(
            "<CAU>ES1234000000000001JN0FA001",
            "<CAU>{0}".format(gurb_cau)
        )

        # Import XML
        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m2_05_xml, "m205_new.xml"
        )

        # Assertions
        self.assertIsNotNone(step_id)
        self.assertEqual(sgc_0002.state, "active")

    @mock.patch("som_gurb.models.giscedata_switching.is_unidirectional_colective_autocons_change")
    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def test_create_from_xml_m2_05_does_not_activate_unrelated_autoconsum(
            self, mock_send_gurb_activation_email, mock_is_unidirectional):
        mock_send_gurb_activation_email.return_value = False
        mock_is_unidirectional.return_value = False
        unrelated_cau = "ES0031241774219778BJA000"

        sw_obj = self.openerp.pool.get("giscedata.switching")
        sgc_obj = self.openerp.pool.get("som.gurb.cups")
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        contract_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")

        sgc_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002")[1]

        sgc_0002 = sgc_obj.browse(self.cursor, self.uid, sgc_id)
        sgc_0002.send_signal("button_create_cups")
        sgc_0002.send_signal("button_activate_cups")

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
        m2_05_xml = m2_05_xml.replace(
            "<CAU>ES1234000000000001JN0FA001",
            "<CAU>{0}".format(unrelated_cau)
        )

        step_id = sw_obj.importar_xml(
            self.cursor, self.uid, m2_05_xml, "m205_new.xml"
        )

        self.assertIsNotNone(step_id)
        self.assertEqual(sgc_0002.state, "active")
        self.assertFalse(mock_send_gurb_activation_email.called)

    def _prepare_m105_cancellation_import(self, matching_cau=True):
        cups_o = self.openerp.pool.get("som.gurb.cups")
        pol_o = self.openerp.pool.get("giscedata.polissa")
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        refs = self.get_references()
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn, pol_id="polissa_tarifa_018")
        self.update_polissa_distri(self.txn, pol_ref="polissa_tarifa_018")
        self.activar_polissa_CUPS()
        cups_o.send_signal(self.cursor, self.uid, [refs["gurb_cups_id"]], [
            "button_create_cups", "button_activate_cups",
        ])
        cups_o.add_service_to_contract(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-02-01"
        )
        service_ids = service_o.search(
            self.cursor, self.uid, [("polissa_id", "=", refs["pol_id"])]
        )
        self.assertEqual(len(service_ids), 1)
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        pol = pol_o.browse(self.cursor, self.uid, refs["pol_id"])
        path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "m105_canvi_autoconsum.xml"
        )
        with open(path, "r") as xml_file:
            xml = xml_file.read()
        cau = cups.gurb_cau_id.self_consumption_id.cau
        self.assertTrue(cau)
        if not matching_cau:
            imd_o = self.openerp.pool.get("ir.model.data")
            autoconsum_o = self.openerp.pool.get("giscedata.autoconsum")
            autoconsum_id = imd_o.get_object_reference(
                self.cursor, self.uid, "giscedata_cups",
                "autoconsum_cups_tarifa_018_autoconsum_41"
            )[1]
            self.assertTrue(autoconsum_id)
            cau = autoconsum_o.read(self.cursor, self.uid, autoconsum_id, ["cau"])["cau"]
            self.assertTrue(cau)
            self.assertNotEqual(cau, cups.gurb_cau_id.self_consumption_id.cau)
        root = etree.fromstring(xml)
        namespace = "{{{0}}}".format(etree.QName(root).namespace)
        cups_nodes = root.findall("./{0}Cabecera/{0}CUPS".format(namespace))
        cau_nodes = root.findall(".//{0}DatosCAU/{0}CAU".format(namespace))
        subseccio_nodes = root.findall(".//{0}DatosCAU/{0}TipoSubseccion".format(namespace))
        self.assertEqual(len(cups_nodes), 1)
        self.assertEqual(len(cau_nodes), 1)
        self.assertEqual(len(subseccio_nodes), 1)
        self.assertTrue(pol.cups.name)
        cups_nodes[0].text = pol.cups.name
        cau_nodes[0].text = cau
        subseccio_nodes[0].text = "0C"
        xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True)
        return refs, xml, service_ids[0]

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def test_m105_matching_cancellation_terminates_service(self, activation_email):
        refs, xml, service_id = self._prepare_m105_cancellation_import()
        cups_o = self.openerp.pool.get("som.gurb.cups")
        sw_o = self.openerp.pool.get("giscedata.switching")
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        root = etree.fromstring(xml)
        namespace = "{{{0}}}".format(etree.QName(root).namespace)
        request_nodes = root.findall("./{0}Cabecera/{0}CodigoDeSolicitud".format(namespace))
        self.assertEqual(len(request_nodes), 1)
        request_code = request_nodes[0].text
        self.assertTrue(request_code)
        context = {"gurb_cancellation_confirmed": False}
        sw_o.importar_xml(
            self.cursor, self.uid, xml, "m105_cancellation.xml", context=context
        )
        self.assertFalse(context["gurb_cancellation_confirmed"])
        sw_ids = sw_o.search(self.cursor, self.uid, [
            ("proces_id.name", "=", "M1"),
            ("step_id.name", "=", "05"),
            ("codi_sollicitud", "=", request_code),
        ])
        self.assertEqual(len(sw_ids), 1)
        step_o = self.openerp.pool.get("giscedata.switching.m1.05")
        step_ids = step_o.search(self.cursor, self.uid, [("sw_id", "=", sw_ids[0])])
        self.assertEqual(len(step_ids), 1)
        step = step_o.browse(self.cursor, self.uid, step_ids[0])
        self.assertEqual(step.dades_cau[0].tipus_subseccio, "0C")
        self.assertEqual(step.dades_cau[0].cau, cups.gurb_cau_id.self_consumption_id.cau)
        self.assertFalse(step.header_id.notificacio_pendent)
        cups = cups_o.browse(
            self.cursor, self.uid, refs["gurb_cups_id"], context={"active_test": False}
        )
        self.assertEqual(cups.state, "cancel")
        self.assertFalse(cups.active)
        self.assertEqual(cups.end_date, step.data_activacio)
        beta = self.openerp.pool.get("som.gurb.cups.beta").browse(
            self.cursor, self.uid, refs["gurb_cups_beta_2_id"]
        )
        self.assertFalse(beta.active)
        self.assertEqual(beta.end_date, step.data_activacio)
        self.assertEqual(service_o.read(
            self.cursor, self.uid, service_id, ["data_fi"]
        )["data_fi"], step.data_activacio)
        activation_email.assert_not_called()

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def test_m105_pending_modification_cancellation_does_not_activate_beta(self, activation_email):
        refs, xml, service_id = self._prepare_m105_cancellation_import()
        cups_o = self.openerp.pool.get("som.gurb.cups")
        beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        beta_o.activate_future_beta(
            self.cursor, self.uid, refs["gurb_cups_beta_2_id"], "2016-02-01"
        )
        self.create_new_gurb_cups_beta(
            refs["gurb_cups_id"], "2016-04-01", 1.5, 0.5, 0,
            context={"activate": False}
        )
        pending_ids = beta_o.search(self.cursor, self.uid, [
            ("gurb_cups_id", "=", refs["gurb_cups_id"]),
            ("future_beta", "=", True),
            ("active", "=", True),
        ])
        self.assertEqual(len(pending_ids), 1)
        self.assertEqual(cups_o.read(
            self.cursor, self.uid, refs["gurb_cups_id"], ["state"]
        )["state"], "comming_modification")
        beta_ids = [refs["gurb_cups_beta_2_id"], pending_ids[0]]
        self.assertNotEqual(beta_ids[0], beta_ids[1])
        beta_fields = ["start_date", "beta_kw", "extra_beta_kw", "gift_beta_kw", "future_beta"]
        before_betas = [
            beta_o.read(self.cursor, self.uid, beta_id, beta_fields) for beta_id in beta_ids
        ]
        self.assertFalse(before_betas[0]["future_beta"])
        self.assertTrue(before_betas[1]["future_beta"])
        context = {"gurb_cancellation_confirmed": False}

        sw_id, info = self.openerp.pool.get("giscedata.switching").importar_xml(
            self.cursor, self.uid, xml, "m105_pending_modification_cancellation.xml",
            context=context
        )

        step = self._get_imported_m105(sw_id)
        self.assertLessEqual(before_betas[1]["start_date"], step.data_activacio)
        helper_o = self.openerp.pool.get("giscedata.switching.helpers")
        result = helper_o.m105_acord_repartiment_autoconsum(self.cursor, self.uid, sw_id)
        self.assertEqual(result[0], "OK")
        cups = cups_o.browse(
            self.cursor, self.uid, refs["gurb_cups_id"], context={"active_test": False}
        )
        self.assertEqual(cups.state, "cancel")
        self.assertFalse(cups.active)
        self.assertEqual(cups.end_date, step.data_activacio)
        self.assertEqual(
            [beta_o.read(self.cursor, self.uid, beta_id, beta_fields) for beta_id in beta_ids],
            before_betas
        )
        for beta in beta_o.browse(self.cursor, self.uid, beta_ids):
            self.assertFalse(beta.active)
            self.assertEqual(beta.end_date, step.data_activacio)
        self.assertEqual(service_o.read(
            self.cursor, self.uid, service_id, ["data_fi"]
        )["data_fi"], step.data_activacio)
        self.assertEqual(service_o.search(
            self.cursor, self.uid, [("polissa_id", "=", refs["pol_id"])]
        ), [service_id])
        self.assertFalse(self._get_imported_m105(sw_id).header_id.notificacio_pendent)
        self.assertFalse(context["gurb_cancellation_confirmed"])
        activation_email.assert_not_called()

    def _get_imported_m105(self, sw_id):
        step_o = self.openerp.pool.get("giscedata.switching.m1.05")
        step_ids = step_o.search(self.cursor, self.uid, [("sw_id", "=", sw_id)])
        self.assertEqual(len(step_ids), 1)
        return step_o.browse(self.cursor, self.uid, step_ids[0])

    def _assert_gurb_service_open(self, refs, service_id, state="active"):
        cups = self.openerp.pool.get("som.gurb.cups").browse(
            self.cursor, self.uid, refs["gurb_cups_id"]
        )
        self.assertEqual(cups.state, state)
        self.assertTrue(cups.active)
        self.assertFalse(cups.end_date)
        beta = self.openerp.pool.get("som.gurb.cups.beta").browse(
            self.cursor, self.uid, refs["gurb_cups_beta_2_id"]
        )
        self.assertTrue(beta.active)
        self.assertFalse(beta.end_date)
        self.assertFalse(self.openerp.pool.get("giscedata.facturacio.services").read(
            self.cursor, self.uid, service_id, ["data_fi"]
        )["data_fi"])

    def test_m105_foreign_cancellation_keeps_gurb_service(self):
        self._check_m105_foreign_cancellation()

    def test_m105_mixed_caus_only_foreign_cancellation_keeps_gurb_service(self):
        self._check_m105_foreign_cancellation(include_gurb_cau=True)

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def _check_m105_foreign_cancellation(self, activation_email, include_gurb_cau=False):
        refs, xml, service_id = self._prepare_m105_cancellation_import(matching_cau=False)
        cups = self.openerp.pool.get("som.gurb.cups").browse(
            self.cursor, self.uid, refs["gurb_cups_id"]
        )
        if include_gurb_cau:
            root = etree.fromstring(xml)
            namespace = "{{{0}}}".format(etree.QName(root).namespace)
            cau_data = root.findall(".//{0}DatosCAU".format(namespace))
            self.assertEqual(len(cau_data), 1)
            gurb_data = deepcopy(cau_data[0])
            gurb_data.find(namespace + "CAU").text = cups.gurb_cau_id.self_consumption_id.cau
            gurb_data.find(namespace + "TipoSubseccion").text = "10"
            cau_data[0].addnext(gurb_data)
            xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True)
        sw_id, info = self.openerp.pool.get("giscedata.switching").importar_xml(
            self.cursor, self.uid, xml, "m105_foreign_cancellation.xml"
        )
        step = self._get_imported_m105(sw_id)
        self.assertEqual(len(step.dades_cau), 2 if include_gurb_cau else 1)
        cancellations = [cau for cau in step.dades_cau if cau.tipus_subseccio == "0C"]
        self.assertEqual(len(cancellations), 1)
        self.assertNotEqual(
            cancellations[0].cau, cups.gurb_cau_id.self_consumption_id.cau
        )
        self._assert_gurb_service_open(refs, service_id)

    def test_m105_cancellation_helper_preserves_active_gurb(self):
        self._check_m105_cancellation_helper()

    def test_m105_cancellation_helper_preserves_atr_pending_gurb(self):
        self._check_m105_cancellation_helper(atr_pending=True)

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def _check_m105_cancellation_helper(self, activation_email, atr_pending=False):
        refs, xml, service_id = self._prepare_m105_cancellation_import(matching_cau=False)
        sw_o = self.openerp.pool.get("giscedata.switching")
        cups_o = self.openerp.pool.get("som.gurb.cups")
        sw_id, info = sw_o.importar_xml(
            self.cursor, self.uid, xml, "m105_helper_cancellation.xml"
        )
        step = self._get_imported_m105(sw_id)
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        # Stage the confirmed CAU data without running the import cancellation route.
        step.dades_cau[0].write({"cau": cups.gurb_cau_id.self_consumption_id.cau})
        if atr_pending:
            cups_o.send_signal(
                self.cursor, self.uid, [refs["gurb_cups_id"]], "button_atr_pending"
            )
        expected_state = "atr_pending" if atr_pending else "active"
        self._assert_gurb_service_open(refs, service_id, state=expected_state)
        sw_o.case_open(self.cursor, self.uid, [sw_id])
        self.assertEqual(sw_o.read(self.cursor, self.uid, sw_id, ["state"])["state"], "open")
        step.header_id.write({"notificacio_pendent": True})
        activation_email.reset_mock()
        helper_o = self.openerp.pool.get("giscedata.switching.helpers")
        result = helper_o.m105_acord_repartiment_autoconsum(
            self.cursor, self.uid, sw_id
        )
        self.assertEqual(result, ("OK", u"  * S'ha tancat correctament."))
        self.assertEqual(sw_o.read(self.cursor, self.uid, sw_id, ["state"])["state"], "done")
        self._assert_gurb_service_open(refs, service_id, state=expected_state)
        self.assertFalse(self._get_imported_m105(sw_id).header_id.notificacio_pendent)
        activation_email.assert_not_called()

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.send_gurb_activation_email")
    def test_m105_cancellation_reimport_preserves_closed_records(self, activation_email):
        refs, xml, service_id = self._prepare_m105_cancellation_import()
        sw_o = self.openerp.pool.get("giscedata.switching")
        cups_o = self.openerp.pool.get("som.gurb.cups")
        beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        sw_id, info = sw_o.importar_xml(
            self.cursor, self.uid, xml, "m105_reimport_cancellation.xml"
        )
        context = {"active_test": False}
        step = self._get_imported_m105(sw_id)
        beta_domain = [("gurb_cups_id", "=", refs["gurb_cups_id"])]
        service_domain = [("polissa_id", "=", refs["pol_id"])]
        beta_ids = beta_o.search(self.cursor, self.uid, beta_domain, context=context)
        service_ids = service_o.search(self.cursor, self.uid, service_domain, context=context)
        self.assertEqual(beta_ids, [refs["gurb_cups_beta_2_id"]])
        self.assertEqual(service_ids, [service_id])
        beta_fields = ["active", "start_date", "end_date"]
        service_fields = ["data_inici", "data_fi", "ultima_modificacio"]
        cups_fields = ["active", "state", "end_date"]
        before_cups = cups_o.read(self.cursor, self.uid, refs["gurb_cups_id"], cups_fields)
        self.assertEqual(before_cups["state"], "cancel")
        self.assertFalse(before_cups["active"])
        self.assertEqual(before_cups["end_date"], step.data_activacio)
        before_betas = beta_o.read(self.cursor, self.uid, beta_ids, beta_fields)
        before_services = service_o.read(self.cursor, self.uid, service_ids, service_fields)
        self.assertEqual(before_betas[0]["end_date"], step.data_activacio)
        self.assertEqual(before_services[0]["data_fi"], step.data_activacio)
        # Exact duplicate steps are rejected upstream, before GURB processing.
        # Keep the fixture transaction intact while exercising that real rejection.
        with avoid_creating_subcursors(self.cursor):
            with mock.patch.object(self.cursor, "rollback"):
                with self.assertRaises(osv.except_osv) as error:
                    super(GiscedataSwitching, sw_o).importar_xml(
                        self.cursor, self.uid, xml, "m105_reimport_cancellation.xml"
                    )
        self.assertEqual(error.exception.value, u"Fitxer processat anteriorment.")
        self.assertEqual(self._get_imported_m105(sw_id).id, step.id)
        self.assertEqual(
            beta_o.search(self.cursor, self.uid, beta_domain, context=context), beta_ids
        )
        self.assertEqual(
            service_o.search(self.cursor, self.uid, service_domain, context=context), service_ids
        )
        self.assertEqual(
            cups_o.read(self.cursor, self.uid, refs["gurb_cups_id"], cups_fields), before_cups
        )
        self.assertEqual(beta_o.read(self.cursor, self.uid, beta_ids, beta_fields), before_betas)
        self.assertEqual(
            service_o.read(self.cursor, self.uid, service_ids, service_fields), before_services
        )
        activation_email.assert_not_called()

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
