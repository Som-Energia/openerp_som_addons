# -*- coding: utf-8 -*-
from datetime import datetime
from yamlns import namespace as ns

from destral import testing
from destral.transaction import Transaction


class TestPaymentMandateSom(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.payment_mandate_o = self.model("payment.mandate")

        imd_obj = self.model('ir.model.data')
        partner_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'base', 'res_partner_asus'
        )[1]

        partner_o = self.model("res.partner")
        partner_o.write(self.cursor, self.uid, partner_id, {'vat': 'ES69324303A'})
        self.partner = partner_o.browse(self.cursor, self.uid, partner_id)

    def tearDown(self):
        self.txn.stop()

    from .utils import assertNsEqual  # legacy gkwh method of abstacting this method

    def test_get_or_create_payment_mandate_called_twice_returns_same(self):
        iban = 'ES8901825726580208779553'
        purpose = 'GENERATION kWh'
        creditor_code = 'CREDITORCODE'
        mandate1_id = self.payment_mandate_o.get_or_create_payment_mandate(
            self.cursor, self.uid, self.partner.id, iban, purpose, creditor_code)
        mandate2_id = self.payment_mandate_o.get_or_create_payment_mandate(
            self.cursor, self.uid, self.partner.id, iban, purpose, creditor_code)
        self.assertEqual(mandate1_id, mandate2_id)

    def test_get_or_create_payment_mandate_not_open_creates_a_new_one(self):
        iban = 'ES8901825726580208779553'
        purpose = 'GENERATION kWh'
        creditor_code = 'CREDITORCODE'
        mandate1_id = self.payment_mandate_o.get_or_create_payment_mandate(
            self.cursor, self.uid, self.partner.id, iban, purpose, creditor_code)
        self.payment_mandate_o.write(
            self.cursor, self.uid, mandate1_id, dict(date_end='2015-01-01'))
        mandate2_id = self.payment_mandate_o.get_or_create_payment_mandate(
            self.cursor, self.uid, self.partner.id, iban, purpose, creditor_code)
        self.assertNotEqual(mandate1_id, mandate2_id)

    def test_get_or_create_payment_mandate_newly_created_has_proper_fields(self):
        self.model("res.partner")

        iban = 'ES8901825726580208779553'
        purpose = 'GENERATION kWh'
        creditor_code = 'CREDITORCODE'

        old_mandate_id = self.payment_mandate_o.get_or_create_payment_mandate(
            self.cursor, self.uid, self.partner.id, iban, purpose, creditor_code)
        # Ensure the next is new
        self.payment_mandate_o.write(
            self.cursor, self.uid, old_mandate_id, dict(date_end='2015-01-01'))

        mandate_id = self.payment_mandate_o.get_or_create_payment_mandate(
            self.cursor, self.uid, self.partner.id, iban, purpose, creditor_code)

        mandate = ns(self.payment_mandate_o.read(self.cursor, self.uid, mandate_id, []))
        self.assertTrue(mandate.name
                        and all(x in 'abdcdef1234567890' for x in mandate.name),
                        "mandate.name should be a lowercase hex code")
        mandate.creditor_id = mandate.creditor_id[1]
        nom_complet = self.partner.name
        self.assertNsEqual(mandate, u"""\
                creditor_address: CHAUSSEE DE NAMUR 40 1367 GEROMPONT (BELGIUM)
                creditor_code: CREDITORCODE
                creditor_id: Tiny sprl
                date: '{today}'
                date_end: false
                debtor_address: 'TANG, 31 HONG KONG STREET 23410 TAIWAN'
                debtor_country: 'TAIWAN'
                debtor_iban: {iban}
                debtor_iban_print: {format_iban}
                debtor_name: {debtor_name}
                debtor_state: ''
                debtor_vat: {vat}
                id: {id}
                mandate_scheme: core
                name: {name}
                notes: GENERATION kWh
                payment_type: recurring
                reference: res.partner,{partner_id}
                signed: true
                """.format(
            id=mandate_id,
            name=mandate.name,  # always change
            partner_id=self.partner.id,
            vat=self.partner.vat,
            debtor_name=nom_complet,
            iban=iban,
            format_iban=' '.join(
                iban[n:n + 4] for n in xrange(0, len(iban), 4)),
            today=datetime.today().strftime("%Y-%m-%d"),
        ))
