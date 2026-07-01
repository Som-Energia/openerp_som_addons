# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import base64
import mock

from som_polissa_condicions_generals.report.giscedata_crm_lead_contract_summary import (
    LeadContractSummaryReport,
)

from .base_som_lead_www import BaseSomLeadWwwTest


_netsvc_local_service = (
    'som_leads_polissa.models.giscedata_crm_lead.netsvc.LocalService'
)


class TestContractSummaryPdf(BaseSomLeadWwwTest):
    class NonTransactionalCursor(object):
        def __init__(self, dbname):
            self.dbname = dbname

        def savepoint(self, *args, **kwargs):
            raise AssertionError("Incoming cursor savepoint should not be used")

        def rollback(self, *args, **kwargs):
            raise AssertionError("Incoming cursor rollback should not be used")

    @mock.patch(_netsvc_local_service)
    def test_contract_summary_pdf_returns_pdf_and_rolls_back_temp_entities(
        self, mock_local_service
    ):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        fake_pdf = b"%PDF-contract-summary"
        mock_local_service.return_value.create.return_value = (fake_pdf, "pdf")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead_id = result["lead_id"]

        pdf_result = lead_o.contract_summary_pdf(self.cursor, self.uid, [lead_id], context={})
        lead = lead_o.browse(self.cursor, self.uid, lead_id)

        self.assertEqual(base64.b64decode(pdf_result["contract_summary"]), fake_pdf)
        self.assertFalse(lead.polissa_id)

    @mock.patch(_netsvc_local_service)
    def test_contract_summary_pdf_uses_summary_report_service(self, mock_local_service):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        mock_local_service.return_value.create.return_value = (b"%PDF-contract-summary", "pdf")
        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)

        lead_o.contract_summary_pdf(self.cursor, self.uid, [result["lead_id"]], context={})

        mock_local_service.assert_called_with('report.giscedata.polissa.contract.summary')

    @mock.patch(_netsvc_local_service)
    def test_report_wrapper_uses_owned_transaction_for_non_transactional_cursor(
        self, mock_local_service
    ):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        report = LeadContractSummaryReport("report.giscedata.crm.lead.contract.summary.test")
        fake_cursor = self.NonTransactionalCursor(self.cursor.dbname)

        fake_pdf = b"%PDF-contract-summary"
        mock_local_service.return_value.create.return_value = (fake_pdf, "pdf")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead_id = result["lead_id"]

        pdf_content, file_format = report.create(fake_cursor, self.uid, [lead_id], {}, context={})
        lead = lead_o.browse(self.cursor, self.uid, lead_id)

        self.assertEqual(pdf_content, fake_pdf)
        self.assertEqual(file_format, "pdf")
        self.assertFalse(lead.polissa_id)
