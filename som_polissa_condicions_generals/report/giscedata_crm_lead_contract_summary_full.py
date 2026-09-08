# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64

import pooler
from report import interface
from service.security import Sudo


class LeadContractSummaryFullReport(interface.report_int):
    def create(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)
        lead_obj = pool.get("giscedata.crm.lead")
        try:
            result = lead_obj.contract_summary_full_pdf(
                cr, uid, ids, context=context, datas=data
            )
        except Exception as error:
            try:
                group_id = pool.get("ir.model.data").get_object_reference(
                    cr,
                    uid,
                    "giscedata_crm_leads",
                    "group_giscedata_crm_lead_allow_print",
                )[1]
                with Sudo(uid=uid, gid=group_id):
                    result = lead_obj.contract_summary_full_pdf(
                        cr, 1, ids, context=context, datas=data
                    )
            except Exception:
                raise error
        return base64.b64decode(result["contract_summary_full"]), "pdf"


LeadContractSummaryFullReport(
    "report.giscedata.crm.lead.contract.summary.full"
)
