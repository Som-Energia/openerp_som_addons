# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class GiscedataSignaturaProcess(osv.osv):
    _inherit = "giscedata.signatura.process"

    def update(self, cursor, uid, ids, context=None):
        result = super(GiscedataSignaturaProcess, self).update(
            cursor, uid, ids, context=context
        )
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        request_obj = self.pool.get("som.holder.change.request")
        request_ids = request_obj.search(
            cursor, uid, [("signature_process_id", "in", ids)], context=context
        )
        for request_id in request_ids:
            request_obj._archive_signed_documents(
                cursor, uid, request_id, context=context
            )
        return result


GiscedataSignaturaProcess()
