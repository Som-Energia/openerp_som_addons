# -*- coding: utf-8 -*-
from osv import osv
from som_indexada.exceptions import indexada_exceptions as exceptions

class GiscedataPolissa(osv.osv):
    _inherit = 'giscedata.polissa'

    def check_modifiable_polissa(
        self, cursor, uid, polissa_id, skip_atr_check=False, excluded_cases=None, context=None
    ):
        """
        Things to check before allowing modcons to the contract.
        - Contract doesn't have ANY pending modcons
        - Contract doesn't have ANY pending ATR cases
        """
        if context is None:
            context = {}

        if excluded_cases is None:
            excluded_cases = []

        sw_obj = self.pool.get('giscedata.switching')

        polissa = self.browse(cursor, uid, polissa_id, context=context)

        if polissa.state != 'activa':
            raise exceptions.PolissaNotActive(polissa.name)

        prev_modcon = polissa.modcontractuals_ids[0]
        if prev_modcon.state == 'pendent':
            raise exceptions.PolissaModconPending(polissa.name)

        excluded_cases.append('R1')
        atr_case = sw_obj.search(cursor, uid, [
            ('polissa_ref_id', '=', polissa.id),
            ('state', 'in', ['open', 'draft', 'pending']),
            ('proces_id.name', 'not in', excluded_cases),
        ])

        if atr_case and not skip_atr_check:
            raise exceptions.PolissaSimultaneousATR(polissa.name)

        return True


GiscedataPolissa()