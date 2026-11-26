# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from destral.testing import OOTestCaseWithCursor
from giscedata_switching.tests.common_tests import TestSwitchingImport
from lxml import etree
from osv import osv


class TestR104Comments(OOTestCaseWithCursor, TestSwitchingImport):
    def setUp(self):
        super(TestR104Comments, self).setUp()
        self.switch(self.txn, "comer")
        contract_id = self.get_contract_id(self.txn)
        step_id = self.create_case_and_step(
            self.cursor, self.uid, contract_id, "R1", "01"
        )
        self.model = self.openerp.pool.get("giscedata.switching.r1.04")
        self.sw_id = self.openerp.pool.get("giscedata.switching.r1.01").read(
            self.cursor, self.uid, step_id, ["sw_id"]
        )["sw_id"][0]

    def create_initial_step(self):
        return self.model.dummy_create(self.cursor, self.uid, self.sw_id)

    def test_initial_step_can_be_created_without_comments(self):
        step_id = self.create_initial_step()
        step = self.model.read(self.cursor, self.uid, step_id, ["comentaris"])
        self.assertFalse(step["comentaris"])

    def test_create_rejects_explicit_empty_comments(self):
        for comments in [False, None, "", " \t\n "]:
            with self.assertRaises(osv.except_osv):
                self.model.create(self.cursor, self.uid, {"comentaris": comments})

    def test_save_rejects_empty_comments(self):
        step_id = self.create_initial_step()
        for comments in [False, None, "", " \t\n "]:
            with self.assertRaises(osv.except_osv) as error:
                self.model.write(self.cursor, self.uid, [step_id], {"comentaris": comments})
            self.assertIn("Comentaris", error.exception.value)

    def test_save_requires_comments_even_if_field_is_omitted(self):
        step_id = self.create_initial_step()
        for vals in [{}, {"num_expedient_escomesa": "123"}]:
            with self.assertRaises(osv.except_osv):
                self.model.write(self.cursor, self.uid, [step_id], vals)

    def test_save_with_comments(self):
        step_id = self.create_initial_step()
        comments = "Adjuntem la documentació sol·licitada."
        self.model.write(self.cursor, self.uid, [step_id], {"comentaris": comments})
        self.model.write(self.cursor, self.uid, [step_id], {"num_expedient_escomesa": "123"})
        self.assertEqual(
            self.model.read(self.cursor, self.uid, step_id, ["comentaris"])["comentaris"],
            comments,
        )

    def test_saved_comments_cannot_be_removed(self):
        step_id = self.create_initial_step()
        self.model.write(self.cursor, self.uid, [step_id], {"comentaris": "Documentació adjunta"})
        for comments in [False, None, "", " \t\n "]:
            with self.assertRaises(osv.except_osv):
                self.model.write(self.cursor, self.uid, step_id, {"comentaris": comments})
        self.assertEqual(
            self.model.read(self.cursor, self.uid, step_id, ["comentaris"])["comentaris"],
            "Documentació adjunta",
        )

    def test_batch_save_requires_comments_on_every_step(self):
        step_ids = [self.create_initial_step(), self.create_initial_step()]
        self.model.write(
            self.cursor, self.uid, [step_ids[0]], {"comentaris": "Documentació adjunta"}
        )
        with self.assertRaises(osv.except_osv):
            self.model.write(self.cursor, self.uid, step_ids, {"num_expedient_escomesa": "123"})
        self.model.write(self.cursor, self.uid, step_ids, {"comentaris": "Documentació adjunta"})

    def test_existing_wizard_still_creates_initial_step(self):
        wizard_model = self.openerp.pool.get("wizard.create.step")
        context = {"active_ids": [self.sw_id]}
        wizard_id = wizard_model.create(self.cursor, self.uid, {"step": "04"}, context=context)
        wizard_model.action_create_steps(self.cursor, self.uid, [wizard_id], context=context)
        step_ids = self.model.search(self.cursor, self.uid, [("sw_id", "=", self.sw_id)])
        self.assertEqual(len(step_ids), 1)
        self.assertFalse(
            self.model.read(self.cursor, self.uid, step_ids[0], ["comentaris"])["comentaris"]
        )

    def test_export_without_comments_shows_clear_error(self):
        step_id = self.create_initial_step()
        for pas_id in [step_id, [step_id], (step_id,)]:
            with self.assertRaises(osv.except_osv) as error:
                self.model.generar_xml(self.cursor, self.uid, pas_id)
            self.assertIn("Comentaris", error.exception.value)

    def test_export_includes_existing_comments_before_documents(self):
        step_id = self.create_initial_step()
        self.model.write(self.cursor, self.uid, [step_id], {
            "comentaris": "Documentació adjunta",
            "document_ids": [(0, 0, {"type": "01", "url": "https://example.org/document.pdf"})],
        })
        name, xml = self.model.generar_xml(self.cursor, self.uid, step_id)
        if not isinstance(xml, bytes):
            xml = xml.encode("iso-8859-1")
        root = etree.fromstring(xml)
        ns = {"r1": "http://localhost/elegibilidad"}
        info = root.find("r1:EnvioInformacionReclamacion", ns)
        comments = info.find("r1:Comentarios", ns)
        documents = info.find("r1:RegistrosDocumento", ns)
        self.assertEqual(comments.text, "Documentació adjunta")
        self.assertIsNotNone(documents)
        self.assertLess(list(info).index(comments), list(info).index(documents))
