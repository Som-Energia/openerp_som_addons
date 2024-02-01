# -*- coding: utf-8 -*-

from osv import osv


class WizardMoveContractsToPrevLot(osv.osv_memory):
    _name = "wizard.move.contracts.prev.lot"
    _inherit = "wizard.move.contracts.prev.lot"

    def move_one_contract_to_prev_lot(self, cursor, uid, id, pol_id, context):
        if not context:
            pass
        clot_o = self.pool.get("giscedata.facturacio.contracte_lot")
        clot_id = super(WizardMoveContractsToPrevLot, self).move_one_contract_to_prev_lot(
            cursor, uid, id, pol_id, context=context
        )
        if context.get("incrementar_n_retrocedir", True):
            clot_n_retrocedit = clot_o.read(cursor, uid, clot_id, ["n_retrocedir_lot"])[
                "n_retrocedir_lot"
            ]
            clot_o.write(cursor, uid, [clot_id], {"n_retrocedir_lot": clot_n_retrocedit + 1})
        return clot_id


WizardMoveContractsToPrevLot()
