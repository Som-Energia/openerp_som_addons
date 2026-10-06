# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

from destral import testing
from destral.transaction import Transaction

from ..models.exceptions import NoSuchUser


class SomreOvUsersTests(testing.OOTestCase):

    base_costumer_vat = 'ES48591264S'
    base_staff_vat = 'G78525764'

    def setUp(self):
        self.pool = self.openerp.pool
        self.imd = self.pool.get('ir.model.data')
        self.res_partner = self.pool.get('res.partner')
        self.users = self.pool.get('somre.ov.users')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.maxDiff = None

    def tearDown(self):
        self.txn.stop()

    def reference(self, module, id):
        return self.imd.get_object_reference(
            self.cursor, self.uid, module, id,
        )[1]

    def test__get_user_login_info__user_exists_and_is_active(self):
        username = self.base_costumer_vat

        result = self.users.identify_login(self.cursor, self.uid, username)

        expected_result = dict(
            vat=self.base_costumer_vat,
            name='Benedetti, Mario',
            email='test@test.test',
            roles=['customer'],
            username=username,
        )
        self.assertEqual(expected_result, result)

    def test__get_user_login_info__user_exists_is_active_and_staff(self):
        username = self.base_staff_vat

        result = self.users.identify_login(self.cursor, self.uid, username)

        expected_result = dict(
            vat=self.base_staff_vat,
            name='Hari, Mata',
            email='matahari@somenergia.coop',
            roles=['staff'],
            username=username,
        )
        self.assertEqual(expected_result, result)

    def test__get_user_login_info__user_exists_and_is_not_active(self):
        res_partner_address_soci_not_active_vat = 'ES14763905K'

        result = self.users.identify_login(
            self.cursor, self.uid, res_partner_address_soci_not_active_vat)

        self.assertEqual(result['code'], 'NoSuchUser')

    def test__get_user_login_info__user_does_not_exists(self):
        res_partner_soci_not_exists_vat = 'ES12345678A'

        result = self.users.identify_login(self.cursor, self.uid, res_partner_soci_not_exists_vat)

        self.assertEqual(result['code'], 'NoSuchUser')

    def test__get_profile(self):
        username = self.base_costumer_vat

        result = self.users.get_profile(self.cursor, self.uid, username)
        expected_result = dict(
            vat=self.base_costumer_vat,
            name='Benedetti, Mario',
            email='test@test.test',
            address='Rincón de Haikus, 23',
            city='Paso de los Toros',
            zip='08600',
            state='Granada',
            phones=['933333333', '666666666'],
            roles=['customer'],
            username=username,
            proxy_vat=None,
            proxy_name=None,
            signed_documents=[],
        )

        self.assertEqual(expected_result, result)

    def test__get_profile__without_phone_numbers(self):
        username = self.base_costumer_vat
        # TODO: use reference()
        # get address id
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', self.base_costumer_vat)]
        )
        partner = self.res_partner.browse(self.cursor, self.uid, partner_id)[0]
        address_id = partner.address[0].id

        # overwrite values
        res_partner_address_model = self.pool.get('res.partner.address')
        res_partner_address_model.write(self.cursor, self.uid, address_id, {
                                        'phone': False, 'mobile': False})

        result = self.users.get_profile(self.cursor, self.uid, username)
        expected_result = dict(
            vat=self.base_costumer_vat,
            name='Benedetti, Mario',
            email='test@test.test',
            address='Rincón de Haikus, 23',
            city='Paso de los Toros',
            zip='08600',
            state='Granada',
            phones=[],
            roles=['customer'],
            username=username,
            proxy_vat=None,
            proxy_name=None,
            signed_documents=[],
        )
        self.assertEqual(expected_result, result)

    def test__get_profile__with_legal_proxy(self):
        username = 'ESW2796397D'

        result = self.users.get_profile(self.cursor, self.uid, username)
        expected_result = dict(
            vat='ESW2796397D',
            name='ACME Industries',
            email='info@acme.com',
            address='Cañon, 12',
            city='El Camino',
            zip='08600',
            state='Granada',
            phones=['933333333', '666666666'],
            roles=['customer'],
            username='ESW2796397D',
            proxy_vat='ES36464471H',
            proxy_name='Aplastado, Coyote',
            signed_documents=[],
        )
        self.assertEqual(expected_result, result)

    def test__get_profile__user_is_staff(self):
        username = self.base_staff_vat

        result = self.users.get_profile(self.cursor, self.uid, username)
        expected_result = dict(
            vat=username,
            name='Hari, Mata',
            email='matahari@somenergia.coop',
            address='Carrer Riu Güell, 68',
            city='Girona',
            zip='17002',
            state='Girona',
            phones=[],
            roles=['staff'],
            username=username,
            proxy_vat=None,
            proxy_name=None,
            signed_documents=[],
        )
        self.assertEqual(expected_result, result)

    def test__sign_document__all_ok(self):
        username = self.base_costumer_vat

        result = self.users.sign_document(self.cursor, self.uid, username, 'RGPD_OV_REPRESENTA')

        self.assertEqual(result, dict(
            signed_version='2023-11-09 00:00:00',
        ))

    def test__sign_document__signs_last_document_version(self):
        username = self.base_costumer_vat
        document_type_id = self.reference(
            "somre_ov_module",
            "type_ovrepresenta_rgpd"
        )
        document_version_obj = self.pool.get('somre.ov.signed.document.type.version')
        document_version_obj.create(self.cursor, self.uid, dict(
            type=document_type_id,
            date='2040-03-02',
        ))

        result = self.users.sign_document(self.cursor, self.uid, username, 'RGPD_OV_REPRESENTA')

        self.assertEqual(result, dict(
            signed_version='2040-03-02 00:00:00',
        ))

    def test__sign_document__wrong_customer(self):
        username = 'NOTEXISTING'

        result = self.users.sign_document(self.cursor, self.uid, username, 'RGPD_OV_REPRESENTA')

        self.assertEqual(result, dict(
            code='NoSuchUser',
            error='User does not exist',
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    def test__sign_document__document_without_version(self):
        username = self.base_costumer_vat

        version_id = self.reference(
            "somre_ov_module",
            "version_type_ovrepresenta_rgpd_2023"
        )
        print("version_ids", version_id)
        document_version_obj = self.pool.get('somre.ov.signed.document.type.version')
        document_version_obj.unlink(self.cursor, self.uid, version_id)

        result = self.users.sign_document(self.cursor, self.uid, username, 'RGPD_OV_REPRESENTA')

        self.assertEqual(result, dict(
            code='NoDocumentVersions',
            error='Document RGPD_OV_REPRESENTA has no version available to sign',
            trace=(result or {}).get('trace', "TRACE IS MISSING"),
        ))

    def test__documents_signed_by_customer__no_documents_signed(self):
        username = self.base_costumer_vat
        result = self.users._documents_signed_by_customer(self.cursor, self.uid, username)
        self.assertEqual([], result)

    def test__documents_signed_by_customer__a_documents_signed(self):
        username = self.base_costumer_vat
        self.users.sign_document(self.cursor, self.uid, username, 'RGPD_OV_REPRESENTA')

        result = self.users._documents_signed_by_customer(self.cursor, self.uid, username)

        self.assertEqual([
            dict(
                document='RGPD_OV_REPRESENTA',
                version='2023-11-09 00:00:00',
            ),
        ], result)

    def test__documents_signed_by_customer__wrong_customer(self):
        username = 'NOTEXISTING'

        with self.assertRaises(NoSuchUser) as ctx:
            self.users._documents_signed_by_customer(self.cursor, self.uid, username)

        self.assertEqual(format(ctx.exception), "User does not exist")

    def test__documents_signed_by_customer__filter_other_customer_signatures(self):
        username = self.base_costumer_vat
        other = 'ESW2796397D'
        self.users.sign_document(self.cursor, self.uid, other, 'RGPD_OV_REPRESENTA')

        result = self.users._documents_signed_by_customer(self.cursor, self.uid, username)

        self.assertEqual([], result)

    def test__sign_document__returned_in_profile(self):
        username = self.base_costumer_vat
        self.users.sign_document(self.cursor, self.uid, username, 'RGPD_OV_REPRESENTA')

        result = self.users.get_profile(self.cursor, self.uid, username)
        expected_result = dict(
            vat=self.base_costumer_vat,
            name='Benedetti, Mario',
            email='test@test.test',
            address='Rincón de Haikus, 23',
            city='Paso de los Toros',
            zip='08600',
            state='Granada',
            phones=['933333333', '666666666'],
            roles=['customer'],
            username=username,
            proxy_vat=None,
            proxy_name=None,
            signed_documents=[
                dict(
                    document='RGPD_OV_REPRESENTA',
                    version='2023-11-09 00:00:00',
                ),
            ],
        )

        self.assertEqual(expected_result, result)
