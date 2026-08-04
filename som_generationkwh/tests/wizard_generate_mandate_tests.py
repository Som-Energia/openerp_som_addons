# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import json
import generationkwh.investmentmodel as gkwh

class TestsWizardGenerateMandate(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        self.maxDiff = None

    def tearDown(self):
        self.txn.stop()

    def get_object_id(self, module, obj_ref):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        irmd_o = pool.get('ir.model.data')
        object_id = irmd_o.get_object_reference(cursor, uid, module, obj_ref)[1]
        return object_id

    def get_existing_mandates(self, partner_id, iban, purpose, creditor_code):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        ResPartner = pool.get("res.partner")
        PaymentMandate = pool.get("payment.mandate")
        partner = ResPartner.read(cursor, uid, partner_id, ['address', 'name', 'vat'])

        search_params = [
            ('debtor_iban', '=', iban),
            ('debtor_vat', '=', partner['vat']),
            ('date_end', '=', False),
            ('reference', '=', 'res.partner,{}'.format(partner_id)),
            ('notes', '=', purpose),
        ]
        mandate_ids = PaymentMandate.search(cursor, uid, search_params)
        return mandate_ids


    def test_create_new_mandate(self):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        soci_o = pool.get('somenergia.soci')
        partner_o = pool.get('res.partner')
        wiz_o = pool.get('wizard.generate.payment.mandate')

        id_soci = self.get_object_id('som_generationkwh', 'soci_aportacions')
        soci_id = soci_o.browse(cursor, uid, id_soci)
        partner_id = soci_id.partner_id
        bank_id = partner_id.bank_ids[0]

        mandates = self.get_existing_mandates(
            partner_id.id,
            bank_id.iban,
            gkwh.mandatePurposeAmorCobrar,
            gkwh.creditorCode,
        )

        # check partner without mandates
        self.assertEqual(len(mandates), 0)

        # create mandate and check right creation
        context = {'active_id': partner_id.id, 'from_model': 'res.partner'}
        id_wizard = wiz_o.create(cursor, uid, {}, context=context)
        wiz_o.write(cursor, uid, [id_wizard], {
            'bank_id': bank_id.id,
        })
        wiz_id = wiz_o.browse(cursor, uid, id_wizard, context)
        wiz_id.action_generate_mandate()

        mandates = self.get_existing_mandates(
            partner_id.id,
            bank_id.iban,
            gkwh.mandatePurposeAmorCobrar,
            gkwh.creditorCode,
        )

        self.assertEqual(wiz_id.mandate_id.id, mandates[0])

    def test_get_existing_mandate(self):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        soci_o = pool.get('somenergia.soci')
        partner_o = pool.get('res.partner')
        wiz_o = pool.get('wizard.generate.payment.mandate')

        id_soci = self.get_object_id('som_generationkwh', 'soci_aportacions')
        soci_id = soci_o.browse(cursor, uid, id_soci)
        partner_id = soci_id.partner_id
        bank_id = partner_id.bank_ids[0]

        # get mandate
        GenerationkwhInvestment = pool.get('generationkwh.investment')
        id_mandate = GenerationkwhInvestment.get_or_create_payment_mandate(cursor, uid,
            partner_id.id,
            bank_id.iban,
            gkwh.mandatePurposeAmorCobrar,
            gkwh.creditorCode
        )

        # check wizard amndate result with existing one
        context = {'active_id': partner_id.id, 'from_model': 'res.partner'}
        id_wizard = wiz_o.create(cursor, uid, {}, context=context)
        wiz_o.write(cursor, uid, [id_wizard], {
            'bank_id': bank_id.id,
        })
        wiz_id = wiz_o.browse(cursor, uid, id_wizard, context)
        wiz_id.action_generate_mandate()

        self.assertEqual(wiz_id.mandate_id.id, id_mandate)
