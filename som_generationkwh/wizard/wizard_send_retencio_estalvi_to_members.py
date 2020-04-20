# -*- encoding: utf-8 -*-
from tools.translate import _
from osv import osv, fields
from datetime import datetime, timedelta, date


class SendRetencioEstalviToMembers(osv.osv_memory):
    """ Wizard per l'enviament massiu del report de
        retenció sobre estalvis de generationkwh"""

    _name = 'send.retencio.estalvi.to.members.wizard'

    def _get_fiscal_year(self, cursor, uid, context={}):
        year = (datetime.now() - timedelta(days=365)).year
        return str(year)

    def send_email_to_members(self, cursor, uid, ids, context=None):
        active_id = context.get("active_id")
        Soci = self.pool.get("somenergia.soci")
        total_sent = Soci.send_emails_to_investors_with_savings_in_year(cursor, uid, self._get_fiscal_year(cursor, uid, context))

        if total_sent > 0:
            self.write(cursor, uid, ids, {'state': 'ok', 'total_sent': str(total_sent)})
        else:
            self.write(cursor, uid, ids, {'state': 'error'})

    _columns = {
        'state': fields.selection(
            [('init', 'Init'), ('ok', 'Ok'), ('error', 'Error')],
            string='Progress State', translate=False
        ),
        'fiscal_year': fields.char('Any fiscal', size=256, readonly=True),
        'total_sent': fields.char('Total enviats', size=256, readonly=True),
    }

    _defaults = {
        'state': 'init',
        'fiscal_year': _get_fiscal_year,
        'emails_sent': '0',
    }


SendRetencioEstalviToMembers()