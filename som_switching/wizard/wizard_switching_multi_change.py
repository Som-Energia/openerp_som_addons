# -*- coding: utf-8 -*-

from osv import osv
from tools.sql_utils import isolation


class WizardSwitchingMultiChange(osv.osv_memory):
    _name = 'wizard.switching.multi.change'
    _inherit = 'wizard.switching.multi.change'

    @isolation(readonly=True, isolation_level='repeatable_read')
    def perform_atr_change(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        wiz = self.browse(cursor, uid, ids[0], context=context)
        new_state = context.get('new_state', wiz.new_state)

        if new_state != 'cancel':
            return super(WizardSwitchingMultiChange, self).perform_atr_change(
                cursor, uid, ids, context=context
            )

        # We have some special conditions fot switching cancels
        num_cases = len(context.get('active_ids', []))
        updated = num_cases
        output = ''

        for sw_id in context.get('active_ids', []):
            try:
                # As the original wizard, we need to do this because it's in read only
                # mode :/
                osv.osv_pool().execute(
                    cursor.dbname,
                    uid,
                    'giscedata.switching',
                    'case_and_cacs_cancel',
                    [sw_id]
                )
            except osv.except_osv as e:
                updated -= 1
                output += "\n- No s'ha pogut cancel·lar l'ATR {}: {}".format(
                    sw_id, e.value
                )

        output = '{}/{} ATRs cancel·lats'.format(updated, num_cases) + output

        self.write(cursor, uid, ids, {
            'result': output,
            'state': 'end'
        })


WizardSwitchingMultiChange()
