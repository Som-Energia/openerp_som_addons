# -*- coding: utf-8 -*-
from __future__ import absolute_import
import base64
import netsvc
from osv import osv


class ContractHelper(osv.osv_memory):
    _name = "contract.helper"

    def get_contract_pdf(self, cursor, uid, pol_id, context=None):
        if context is None:
            context = {}
        service = netsvc.LocalService('report.giscedata.polissa')
        (result, _doc_format) = service.create(
            cursor, uid, [pol_id], {}, context
        )
        return {'contract': base64.b64encode(result)}


ContractHelper()
