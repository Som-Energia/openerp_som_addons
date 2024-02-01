# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors

import mock
import os


class TestRevertIncidentFactContracteLot(testing.OOTestCase):
    def setUp(self):
        self.openerp.install_module("giscedata_tarifas_pagos_capacidad_20210601")
        self.openerp.install_module("giscedata_tarifas_peajes_20210601")
        self.openerp.install_module("giscedata_tarifas_cargos_20210601")
        os.environ["OORQ_ASYNC"] = "False"
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def _create_c_lot_facturar(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        self.openerp.pool.get("giscedata.lectures.lectura")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        lot_obj = self.openerp.pool.get("giscedata.facturacio.lot")
        clot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        self.openerp.pool.get("giscedata.facturacio.contracte_lot.factura")
        conf_obj = self.openerp.pool.get("res.config")
        contract_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]

        # Configurem algunes variables
        conf_obj.set(cursor, uid, "inici_final_use_lot", 0)

        # Creem lots de facturacio
        lot_obj.crear_lots_mensuals(cursor, uid, 2021)
        lot_id = lot_obj.search(cursor, uid, [("name", "=", "06/2021")], limit=1)[0]

        # Activem el contracte. Les dades que te de demo ja son correctes (si, increible).
        # Fins i tot les lectures
        contract_obj.write(cursor, uid, contract_id, {"lot_facturacio": lot_id})
        contract_obj.send_signal(cursor, uid, [contract_id], ["validar", "contracte"])

        # Intentem valida i facturar a traves del lot de facturacio per facturar el mes 05
        # Validacio
        contracte_lot_id = clot_obj.search(
            cursor, uid, [("polissa_id", "=", contract_id), ("lot_id", "=", lot_id)]
        )
        self.assertEqual(len(contracte_lot_id), 1)
        contracte_lot_id = contracte_lot_id[0]
        clot_obj.write(cursor, uid, contracte_lot_id, {"state": "obert"})
        lot_obj.write(cursor, uid, lot_id, {"state": "obert"})
        with PatchNewCursors():
            clot_obj.wkf_obert(cursor, uid, [contracte_lot_id], {"from_lot": False})
        clot_info = clot_obj.read(cursor, uid, contracte_lot_id, [])
        self.assertEqual(clot_info["state"], "facturar")
        self.assertFalse(clot_info["status"])

        # Facturacio
        with PatchNewCursors():
            clot_obj.facturar(cursor, uid, [contracte_lot_id])
        clot_info = clot_obj.read(cursor, uid, contracte_lot_id, [])
        self.assertEqual(clot_info["state"], "facturat")
        self.assertFalse(clot_info["status"])

        # Comprovem la factura creada
        factura_id = fact_obj.search(cursor, uid, [("lot_facturacio", "=", lot_id)])
        fact_obj.browse(cursor, uid, factura_id)[0]
        return contracte_lot_id, contract_id

    @mock.patch(
        "som_facturacio_comer.wizard.wizard_revert_incident_fact_contracte_lot.WizardRevertIncidentFactCLot.delete_lot_factures_lectures",  # noqa: E501
    )
    def test_do_action__incident_no_data_ultima_lectura_si_fact(self, mock_delete):
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.openerp.pool.get("ir.model.data")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        clot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        wiz_obj = self.openerp.pool.get("wizard.revert.incident.fact.c_lot")
        other_fact_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]
        c_lot_id, pol_id = self._create_c_lot_facturar()
        fact_obj.write(cursor, uid, other_fact_id, {"polissa_id": pol_id})
        clot_obj.write(cursor, uid, c_lot_id, {"state": "facturat_incident"})

        context = {"active_id": c_lot_id, "active_ids": [c_lot_id]}
        vals = {"delete_lectures": False}
        wiz_id = wiz_obj.create(cursor, uid, vals, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        wiz.do_action(context=context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        self.assertEqual(mock_delete.call_count, 0)

        self.assertTrue(u"Pòlisses on actuar: 0\n" in wiz.info)
        self.assertTrue(
            "Pòlissa {} té factures però no té Data última lectura facturada Real. No s'hi actua\n".format(  # noqa: E501
                pol_id
            )
            in wiz.info
        )

    @mock.patch(
        "som_facturacio_comer.wizard.wizard_revert_incident_fact_contracte_lot.WizardRevertIncidentFactCLot.delete_lot_factures_lectures"  # noqa: E501
    )
    def test_do_action__incident_no_data_ultima_lectura_no_fact(self, mock_delete):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        wiz_obj = self.openerp.pool.get("wizard.revert.incident.fact.c_lot")

        c_lot_id, pol_id = self._create_c_lot_facturar()
        clot_obj.write(cursor, uid, c_lot_id, {"state": "facturat_incident"})

        context = {"active_id": c_lot_id, "active_ids": [c_lot_id]}
        vals = {"delete_lectures": False}
        wiz_id = wiz_obj.create(cursor, uid, vals, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        wiz.do_action(context=context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        self.assertEqual(mock_delete.call_count, 1)

        self.assertTrue(u"Pòlisses on actuar: 1\n" in wiz.info)

    def test_delete_lot_factures_lectures__not_delete_lectures(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        wiz_obj = self.openerp.pool.get("wizard.revert.incident.fact.c_lot")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        lect_obj = self.openerp.pool.get("giscedata.lectures.lectura")

        c_lot_id, pol_id = self._create_c_lot_facturar()
        clot_obj.write(cursor, uid, c_lot_id, {"state": "facturat_incident"})

        clot = clot_obj.browse(cursor, uid, c_lot_id)
        lect_pre = lect_obj.search(
            cursor,
            uid,
            [
                ("comptador.polissa", "=", clot.polissa_id.id),
                ("comptador.active", "=", True),
            ],
        )

        context = {"active_id": c_lot_id, "active_ids": [c_lot_id]}
        vals = {"delete_lectures": False}
        wiz_id = wiz_obj.create(cursor, uid, vals, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        context = {"delete_lectures": False}
        wiz.delete_lot_factures_lectures(
            pol_id=clot.polissa_id.id, lot_id=clot.lot_id.id, c_lot_id=c_lot_id, context=context
        )

        lot_fact_ids = fact_obj.search(
            cursor,
            uid,
            [("lot_facturacio", "=", clot.lot_id.id), ("polissa_id", "=", clot.polissa_id.id)],
        )
        clot = clot_obj.browse(cursor, uid, c_lot_id)
        self.assertEqual(lot_fact_ids, [])
        self.assertEqual(clot.state, "obert")

        lect_post = lect_obj.search(
            cursor,
            uid,
            [
                ("comptador.polissa", "=", clot.polissa_id.id),
                ("comptador.active", "=", True),
            ],
        )
        self.assertEqual(lect_pre, lect_post)

    def test_delete_lot_factures_lectures__delete_lectures_no_data_ultima_lect(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        wiz_obj = self.openerp.pool.get("wizard.revert.incident.fact.c_lot")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        lect_obj = self.openerp.pool.get("giscedata.lectures.lectura")

        c_lot_id, pol_id = self._create_c_lot_facturar()
        clot_obj.write(cursor, uid, c_lot_id, {"state": "facturat_incident"})

        clot = clot_obj.browse(cursor, uid, c_lot_id)

        context = {"active_id": c_lot_id, "active_ids": [c_lot_id]}
        vals = {"delete_lectures": True}
        wiz_id = wiz_obj.create(cursor, uid, vals, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        context = {"delete_lectures": True}
        wiz.delete_lot_factures_lectures(
            pol_id=clot.polissa_id.id, lot_id=clot.lot_id.id, c_lot_id=c_lot_id, context=context
        )

        lot_fact_ids = fact_obj.search(
            cursor,
            uid,
            [("lot_facturacio", "=", clot.lot_id.id), ("polissa_id", "=", clot.polissa_id.id)],
        )
        clot = clot_obj.browse(cursor, uid, c_lot_id)
        self.assertEqual(lot_fact_ids, [])
        self.assertEqual(clot.state, "obert")

        lect_post = lect_obj.search(
            cursor,
            uid,
            [
                ("comptador.polissa", "=", clot.polissa_id.id),
            ],
        )
        self.assertEqual(lect_post, [])

    def test_delete_lot_factures_lectures__delete_lectures_si_data_ultima_lect(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        wiz_obj = self.openerp.pool.get("wizard.revert.incident.fact.c_lot")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        lect_obj = self.openerp.pool.get("giscedata.lectures.lectura")

        c_lot_id, pol_id = self._create_c_lot_facturar()
        clot_obj.write(cursor, uid, c_lot_id, {"state": "facturat_incident"})
        clot = clot_obj.browse(cursor, uid, c_lot_id)
        pol_obj.write(cursor, uid, clot.polissa_id.id, {"data_ultima_lectura": "2021-06-01"})
        lect_pre = lect_obj.search(
            cursor,
            uid,
            [("comptador.polissa", "=", clot.polissa_id.id), ("name", ">", "2021-06-01")],
        )
        self.assertTrue(lect_pre)

        context = {"active_id": c_lot_id, "active_ids": [c_lot_id]}
        vals = {"delete_lectures": True}
        wiz_id = wiz_obj.create(cursor, uid, vals, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        context = {"delete_lectures": True}
        wiz.delete_lot_factures_lectures(
            pol_id=clot.polissa_id.id, lot_id=clot.lot_id.id, c_lot_id=c_lot_id, context=context
        )

        lot_fact_ids = fact_obj.search(
            cursor,
            uid,
            [("lot_facturacio", "=", clot.lot_id.id), ("polissa_id", "=", clot.polissa_id.id)],
        )
        clot = clot_obj.browse(cursor, uid, c_lot_id)

        self.assertEqual(lot_fact_ids, [])
        self.assertEqual(clot.state, "obert")

        lect_post = lect_obj.search(
            cursor,
            uid,
            [("comptador.polissa", "=", clot.polissa_id.id), ("name", ">", "2021-06-01")],
        )
        self.assertEqual(lect_post, [])

    def test_delete_lectures__not_lot_factures(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        wiz_obj = self.openerp.pool.get("wizard.revert.incident.fact.c_lot")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        lect_obj = self.openerp.pool.get("giscedata.lectures.lectura")

        c_lot_id, pol_id = self._create_c_lot_facturar()
        clot_obj.write(cursor, uid, c_lot_id, {"state": "finalitzat"})
        clot = clot_obj.browse(cursor, uid, c_lot_id)

        pre_lot_fact_ids = fact_obj.search(
            cursor,
            uid,
            [("lot_facturacio", "=", clot.lot_id.id), ("polissa_id", "=", clot.polissa_id.id)],
        )
        fact_obj.unlink(cursor, uid, pre_lot_fact_ids)

        pol_obj.write(cursor, uid, clot.polissa_id.id, {"data_ultima_lectura": "2021-06-01"})
        lect_pre = lect_obj.search(
            cursor,
            uid,
            [("comptador.polissa", "=", clot.polissa_id.id), ("name", ">", "2021-06-01")],
        )
        self.assertTrue(lect_pre)

        context = {"active_id": c_lot_id, "active_ids": [c_lot_id]}
        vals = {"delete_lectures": True}
        wiz_id = wiz_obj.create(cursor, uid, vals, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        context = {"delete_lectures": True}
        wiz.delete_lot_factures_lectures(
            pol_id=clot.polissa_id.id, lot_id=clot.lot_id.id, c_lot_id=c_lot_id, context=context
        )

        clot = clot_obj.browse(cursor, uid, c_lot_id)

        self.assertEqual(clot.state, "obert")

        lect_post = lect_obj.search(
            cursor,
            uid,
            [("comptador.polissa", "=", clot.polissa_id.id), ("name", ">", "2021-06-01")],
        )
        self.assertEqual(lect_post, [])
