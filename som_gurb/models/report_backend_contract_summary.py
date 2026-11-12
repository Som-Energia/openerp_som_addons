# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from .report_backend_ccpp import ReportBackendCondicionsParticulars


class ReportBackendContractSummary(ReportBackendCondicionsParticulars):
    _inherit = "report.backend.contract.summary"

    def get_gurb_summary_data(self, cursor, uid, pol, context=None):
        return self.get_gurb(cursor, uid, pol, context=context)


ReportBackendContractSummary()
