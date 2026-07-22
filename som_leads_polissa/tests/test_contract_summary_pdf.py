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

    @mock.patch(_netsvc_local_service)
    def test_contract_summary_full_pdf_uses_combined_service_and_rolls_back(
        self, mock_local_service
    ):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        fake_pdf = b"%PDF-contract-summary-and-conditions"
        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        captured = {}
        datas = {'form': {'source': 'lead'}}

        def create(tmp_cursor, service_uid, polissa_ids, data, summary_context):
            temporary_lead = lead_o.browse(
                tmp_cursor, self.uid, result["lead_id"], context=summary_context
            )
            captured["polissa_id"] = temporary_lead.polissa_id.id
            return fake_pdf, "pdf"

        mock_local_service.return_value.create.side_effect = create

        pdf_result = lead_o.contract_summary_full_pdf(
            self.cursor,
            self.uid,
            [result["lead_id"]],
            datas=datas,
            context={"source": "test"}
        )
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(
            base64.b64decode(pdf_result["contract_summary_full"]), fake_pdf
        )
        mock_local_service.assert_called_with(
            'report.giscedata.polissa.contract.summary.full'
        )
        service_args = mock_local_service.return_value.create.call_args[0]
        self.assertEqual(service_args[2], [captured["polissa_id"]])
        self.assertIs(service_args[3], datas)
        self.assertEqual(service_args[4], {
            "source": "test",
            "lead": True,
            "lang": "es_ES",
            "in_rollback_transaction": True,
            "summary_contract": True,
        })
        self.assertFalse(lead.polissa_id)

    @mock.patch(_netsvc_local_service)
    def test_contract_summary_full_pdf_passes_provisional_tariff_prices(
        self, mock_local_service
    ):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        prices = {
            'preu_fix_energia_p1': 1.01,
            'preu_fix_energia_p2': 1.02,
            'preu_fix_energia_p3': 1.03,
            'preu_fix_energia_p4': 1.04,
            'preu_fix_energia_p5': 1.05,
            'preu_fix_energia_p6': 1.06,
            'preu_fix_potencia_p1': 2.01,
            'preu_fix_potencia_p2': 2.02,
            'preu_fix_potencia_p3': 2.03,
            'preu_fix_potencia_p4': 2.04,
            'preu_fix_potencia_p5': 2.05,
            'preu_fix_potencia_p6': 2.06,
            'set_custom_potencia': True,
            'tipus_tarifa_lead': 'tarifa_provisional',
        }
        lead_o.write(self.cursor, self.uid, [result['lead_id']], prices)
        mock_local_service.return_value.create.return_value = (b'%PDF', 'pdf')

        lead_o.contract_summary_full_pdf(
            self.cursor, self.uid, [result['lead_id']], context={}
        )

        context = mock_local_service.return_value.create.call_args[0][4]
        self.assertEqual(context['tarifa_provisional'], {
            'preus_provisional_energia': {
                'P1': 1.01, 'P2': 1.02, 'P3': 1.03,
                'P4': 1.04, 'P5': 1.05, 'P6': 1.06,
            },
            'preus_provisional_potencia': {
                'P1': 2.01, 'P2': 2.02, 'P3': 2.03,
                'P4': 2.04, 'P5': 2.05, 'P6': 2.06,
            },
        })

    @mock.patch(_netsvc_local_service)
    def test_contract_summary_full_pdf_rolls_back_when_report_fails(
        self, mock_local_service
    ):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        mock_local_service.return_value.create.side_effect = RuntimeError('failed')

        with self.assertRaises(RuntimeError):
            lead_o.contract_summary_full_pdf(
                self.cursor, self.uid, [result['lead_id']], context={}
            )

        lead = lead_o.browse(self.cursor, self.uid, result['lead_id'])
        self.assertFalse(lead.polissa_id)

    @mock.patch(_netsvc_local_service)
    def test_contract_summary_full_pdf_rolls_back_when_entity_creation_fails(
        self, mock_local_service
    ):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)

        with mock.patch.object(
            lead_o, 'create_entities', side_effect=RuntimeError('failed')
        ):
            with self.assertRaises(RuntimeError):
                lead_o.contract_summary_full_pdf(
                    self.cursor, self.uid, [result['lead_id']], context={}
                )

        lead = lead_o.browse(self.cursor, self.uid, result['lead_id'])
        self.assertFalse(lead.polissa_id)
        self.assertFalse(mock_local_service.called)
