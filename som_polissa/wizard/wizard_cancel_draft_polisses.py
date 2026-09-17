# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv, fields
from tools.translate import _


class WizardCancelDraftPolisses(osv.osv_memory):

    _name = "wizard.cancel.draft.polisses"

    def action_cancel_draft_polisses(self, cursor, uid, ids, context=None):
        """Run the draft-policy cancellation cron on demand."""
        if context is None:
            context = {}

        imd_obj = self.pool.get("ir.model.data")
        cron_id = imd_obj.get_object_reference(
            cursor, uid, "som_polissa", "ir_cron_cancel_draft_polisses"
        )[1]
        self.pool.get("ir.cron").execute_cron_call(cursor, uid, cron_id, context=context)
        self.write(
            cursor,
            uid,
            ids,
            {
                "state": "done",
                "info": _("S'ha executat la cancel·lació de pòlisses en esborrany antigues."),
            },
            context=context,
        )
        return True

    _columns = {
        "state": fields.selection(
            [("init", "Inici"), ("done", "Finalitzat")], "Estat", required=True
        ),
        "info": fields.text("Informació", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: _(
            "S'executarà la cancel·lació de les pòlisses que fa més de tres mesos "
            "que són en esborrany."
        ),
    }


WizardCancelDraftPolisses()
