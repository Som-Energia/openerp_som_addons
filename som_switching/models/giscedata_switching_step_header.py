# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class GiscedataSwitchingStepHeader(osv.osv):
    _name = "giscedata.switching.step.header"
    _inherit = "giscedata.switching.step.header"

    def _referenced_rejection_ids(self, cursor, rejection_ids, excluded_ids, context=None):
        if not rejection_ids:
            return set()
        domain = [
            ("id", "not in", excluded_ids),
            ("rebuig_ids", "in", list(rejection_ids)),
        ]
        # Ownership must include headers hidden by the caller's record rules.
        owner_context = dict(context or {}, active_test=False)
        header_ids = self.search(cursor, 1, domain, context=owner_context)
        referenced_ids = set()
        for header in self.read(
            cursor, 1, header_ids, ["rebuig_ids"], context=owner_context
        ):
            referenced_ids.update(header["rebuig_ids"])
        return referenced_ids.intersection(rejection_ids)

    def create(self, cursor, uid, values, context=None):
        header_id = super(GiscedataSwitchingStepHeader, self).create(
            cursor, uid, values, context=context
        )
        rejection_ids = self.read(
            cursor, uid, header_id, ["rebuig_ids"], context=context
        )["rebuig_ids"]
        shared_ids = self._referenced_rejection_ids(
            cursor, rejection_ids, [header_id], context=context
        )
        if shared_ids:
            rejections = self.pool.get("giscedata.switching.rebuig")
            copied_ids = [
                rejections.copy(cursor, uid, rejection_id, context=context)
                if rejection_id in shared_ids else rejection_id
                for rejection_id in rejection_ids
            ]
            self.write(
                cursor, uid, [header_id], {"rebuig_ids": [(6, 0, copied_ids)]},
                context=context,
            )
        return header_id

    def unlink(self, cursor, uid, ids, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        rejection_ids = set()
        for header in self.read(cursor, uid, ids, ["rebuig_ids"], context=context):
            if header["rebuig_ids"]:
                rejection_ids.update(header["rebuig_ids"])
                # Upstream cleanup deletes every rejection still linked here.
                self.write(
                    cursor, uid, [header["id"]], {"rebuig_ids": [(6, 0, [])]},
                    context=context,
                )
        result = super(GiscedataSwitchingStepHeader, self).unlink(
            cursor, uid, ids, context=context
        )
        referenced_ids = self._referenced_rejection_ids(
            cursor, rejection_ids, [], context=context
        )
        orphan_ids = rejection_ids.difference(referenced_ids)
        if orphan_ids:
            self.pool.get("giscedata.switching.rebuig").unlink(
                cursor, uid, list(orphan_ids), context=context
            )
        return result


GiscedataSwitchingStepHeader()
