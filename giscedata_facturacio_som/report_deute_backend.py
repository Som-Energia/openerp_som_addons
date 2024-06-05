# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv


class ReportResumDeuteBackend(osv.osv):
    _inherit = "report.resum.deute.backend"

    def show_pending_state(self):
        return False


ReportResumDeuteBackend()
