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

    def create_from_form(self, cursor, uid,
            partner_id, order_date, amount_in_euros, ip, iban, emissio=None,
            context=None):

        if amount_in_euros <= 0 or amount_in_euros % gkwh.shareValue > 0:
            raise Exception("Invalid amount")
        print iban
        iban = self.check_iban(cursor, uid, iban)
        if not iban:
            print iban
            raise Exception("Wrong iban")

        if not emission:
            emission = 'emissio_apo'

        imd_model = self.pool.get('ir.model.data')
        emission_id = imd_model.get_object_reference(
            cursor, uid, 'som_generationkwh', emission
        )[1]

        Soci = self.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [
                ('partner_id','=',partner_id)
                ])
        if not member_ids:
            raise Exception("Not a member")

        bank_id = self.get_or_create_partner_bank(cursor, uid,
                    partner_id, iban)
        ResPartner = self.pool.get('res.partner')
        ResPartner.write(cursor, uid, partner_id, dict(
            bank_inversions = bank_id,),context)

        ResUser = self.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])
        IrSequence = self.pool.get('ir.sequence')
        name = IrSequence.get_next(cursor,uid,'som.inversions.gkwh')

        inv = InvestmentState(user['name'], datetime.now())
        inv.order(
            name = name,
            date = order_date,
            amount = amount_in_euros,
            iban = iban,
            ip = ip,
            )
        investment_id = self.create(cursor, uid, dict(
            inv.erpChanges(),
            member_id = member_ids[0],
            emission_id = emission_id,
        ), context)

        self.get_or_create_payment_mandate(cursor, uid,
            partner_id, iban, gkwh.mandateName, gkwh.creditorCode)

        self.send_mail(cursor, uid, investment_id,
            'generationkwh.investment', 'generationkwh_mail_creacio')

        return investment_id

InvestmentAportacio()
# vim: et ts=4 sw=4
