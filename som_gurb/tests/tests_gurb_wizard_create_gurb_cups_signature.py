# -*- coding: utf-8 -*-

import mock
from tests_gurb_base import TestsGurbBase


class TestsGurbWizardCreateGurbCupsSignature(TestsGurbBase):

    _start_signature_fnc = (
        "giscedata_signatura_documents_signaturit.giscedata_signatura_documents."
        "GiscedataSignaturaProcess.start"
    )

    @mock.patch(_start_signature_fnc, return_value=True)
    def test_gurb_wizard_create_gurb_cups_signature(self, start_mock):
        wiz_obj = self.openerp.pool.get("wizard.create.gurb.cups.signature")

        ctx = {
            "active_id": self.get_references()["gurb_cups_id"],
            "delivery_type": "url",
        }

        wiz_id = wiz_obj.create(self.cursor, self.uid, {}, context=ctx)
        process_id = wiz_obj.start_signature_process(self.cursor, self.uid, [wiz_id], context=ctx)
        self.assertTrue(process_id)
