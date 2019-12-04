# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, date, timedelta
import generationkwh.investmentmodel as gkwh
from generationkwh.investmentstate import InvestmentState

class InvestmentAportacio(osv.osv):

    _name = 'investment.aportacio'
    _inherit = 'generationkwh.investment'

    def mark_as_signed(self, cursor, uid, id, signed_date=None):
        """
        The investment after ordered is kept in 'draft' state,
        until the customer sign the contract.
        """

        Soci = self.pool.get('somenergia.soci')
        User = self.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        inversio = self.read(cursor, uid, id, [
            'log',
            'draft',
            'actions_log',
            'signed_date',
            ])
        ResUser = self.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])

        signed_date = str(datetime.today().date() + timedelta(days=15))

        inv = InvestmentState(user['name'], datetime.now(),
            log = inversio['log'],
            signed_date = inversio['signed_date'],
        )
        inv.sign(signed_date)
        self.write(cursor, uid, id, inv.erpChanges())

InvestmentAportacio()
# vim: et ts=4 sw=4
