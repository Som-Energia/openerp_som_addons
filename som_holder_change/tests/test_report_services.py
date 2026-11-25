# -*- coding: utf-8 -*-
from __future__ import absolute_import

import netsvc

from destral import testing

from report_puppeteer.report_puppeteer import PuppeteerParser
from som_polissa_condicions_generals.report.giscedata_polissa_contract_summary_full import (
    ContractSummaryFullReport,
)


class TestReportServices(testing.OOTestCase):

    def test_holder_change_reports_are_registered(self):
        ContractSummaryFullReport(
            "report.giscedata.polissa.contract.summary.full"
        )
        PuppeteerParser(
            "report.report_mandato",
            "report.backend.mandat.sepa",
            "som_polissa/report/sepa.mako",
            params={},
        )

        self.assertTrue(
            netsvc.LocalService(
                "report.giscedata.polissa.contract.summary.full"
            )
        )
        self.assertTrue(netsvc.LocalService("report.report_mandato"))
