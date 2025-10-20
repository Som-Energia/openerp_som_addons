# -*- coding: utf-8 -*-
import mock

from destral import testing
from destral.transaction import Transaction

from ..models import res_partner_address


class FakeMailchimpLists:
    def update_list_member(self, list_id, subscriber_hash, client_data):
        pass

    def get_all_lists(self, fields, count):
        pass


class FakeMailchimpClient:
    def __init__(self):
        self.lists = FakeMailchimpLists()


class FakeMD5:
    def __init__(self, s):
        self.string = s

    def hexdigest(self):
        return self.string


fake_mchimp_client = FakeMailchimpClient()


class TestsPartnerAddress(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor, self.uid, self.pool = (self.txn.cursor, self.txn.user, self.openerp.pool)

    def tearDown(self):
        self.txn.stop()

    def test_fill_merge_fields_soci__withoutContract(self):
        rpa_obj = self.pool.get("res.partner.address")
        imd_obj = self.pool.get("ir.model.data")
        address_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_address_soci"
        )[1]
        municipi_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_17160"
        )[1]
        rpa_obj.write(self.cursor, self.uid, address_id, {"id_municipi": municipi_id})

        merge_fields = rpa_obj.fill_merge_fields_soci(
            self.cursor, self.uid, address_id
        )

        self.maxDiff = None
        self.assertDictEqual(
            merge_fields,
            {
                'email_address': u'test@test.test',
                'merge_fields': {
                    'AUTO': 'sense autoproducci\xc3\xb3',
                    'EMAIL': u'test@test.test',
                    'MMERGE1': u'ES97053918J',
                    'MMERGE10': u'972123456',
                    'MMERGE18': '',
                    'MMERGE19': 'No CCVV',
                    'MMERGE22': 'sense_contracte',
                    'MMERGE4': u'S202129',
                    'MMERGE5': u'Pi, Pere',
                    'MMERGE7': u'08600',
                    'MMERGE8': False,
                    'MMERGE9': '',
                    'N_PILA': u'Pere',
                    'MMERGE3': u'Sant Feliu de Gu\xedxols',
                    'MMERGE11': u'Baix Empord\xe0',
                    'MMERGE13': u'Catalu\xf1a',
                    'MMERGE6': u'Girona',
                },
                'status': 'subscribed',
            },
        )

    def test_fill_merge_fields_soci__withContract(self):
        rpa_obj = self.pool.get("res.partner.address")
        imd_obj = self.pool.get("ir.model.data")
        address_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_address_domestic"
        )[1]
        municipi_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_17160"
        )[1]
        rpa_obj.write(self.cursor, self.uid, address_id, {"id_municipi": municipi_id})

        merge_fields = rpa_obj.fill_merge_fields_soci(
            self.cursor, self.uid, address_id
        )

        self.maxDiff = None
        self.assertDictEqual(
            merge_fields,
            {
                'email_address': u'test@test.test',
                'merge_fields': {
                    'AUTO': 'sense autoproducci\xc3\xb3',
                    'EMAIL': u'test@test.test',
                    'MMERGE1': u'ES78106306P',
                    'MMERGE10': u'600000000',
                    'MMERGE18': 'no \xc3\xa9s empresa',
                    'MMERGE19': 'No CCVV',
                    'MMERGE22': 'contracte_esborrany',
                    'MMERGE4': u'S0002',
                    'MMERGE5': u'F\xedsica, Persona',
                    'MMERGE7': u'17800',
                    'MMERGE8': u'en_US',
                    'MMERGE9': 'domestic',
                    'N_PILA': u'Persona',
                    'MMERGE3': u'Sant Feliu de Gu\xedxols',
                    'MMERGE11': u'Baix Empord\xe0',
                    'MMERGE13': u'Catalu\xf1a',
                    'MMERGE6': u'Girona',

                },
                'status': 'subscribed',
            },
        )

    def test_fill_merge_fields_clients(self):
        partner_address_o = self.pool.get("res.partner.address")
        partner_o = self.pool.get("res.partner")
        imd_o = self.pool.get("ir.model.data")
        address_id = imd_o.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_address_1"
        )[1]
        partner_id = partner_address_o.read(self.cursor, self.uid, address_id, ["partner_id"])[
            "partner_id"
        ][0]

        municipi_id = imd_o.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_17160"
        )[1]
        partner_address_o.write(self.cursor, self.uid, address_id, {"id_municipi": municipi_id})

        partner_o.write(self.cursor, self.uid, partner_id, {"lang": "en_US"})
        merge_fields = partner_address_o.fill_merge_fields_clients(
            self.cursor, self.uid, address_id
        )
        self.maxDiff = None
        self.assertDictEqual(
            merge_fields,
            {
                "email_address": u"info@openroad.be",
                "merge_fields": {
                    "EMAIL": u"info@openroad.be",
                    "FNAME": u"OpenRoad",
                    "LNAME": u"OpenRoad",
                    "MMERGE10": u"1000",
                    "MMERGE3": u"en_US",
                    "MMERGE9": u"OpenRoad",
                    "MMERGE5": u"Sant Feliu de Gu\xedxols",
                    "MMERGE6": u"Baix Empord\xe0",
                    "MMERGE7": u"Girona",
                    "MMERGE8": u"Catalu\xf1a",
                },
                "status": "subscribed",
            },
        )

    @mock.patch("som_polissa_soci.models.res_partner_address.md5")
    @mock.patch("som_polissa_soci.tests.tests_partner_address.fake_mchimp_client.lists")
    def test_update_client_email_in_all_lists(self, mock_fakemailchimp, mock_md5):
        subscriber_hash = "12345"
        old_email = "test@test.test"
        new_email = "new@test.test"
        client_data = {"email_address": new_email, "merge_fields": {"EMAIL": new_email}}

        mock_md5.return_value = FakeMD5(subscriber_hash)
        mock_fakemailchimp.get_all_lists.return_value = {
            "lists": [{"id": 1, "name": "som"}, {"id": 2, "name": "som"}]
        }

        partner_address_o = self.pool.get("res.partner.address")
        partner_address_o.update_client_email_in_all_lists(
            self.cursor, self.txn, [1], old_email, new_email, fake_mchimp_client
        )

        mock_fakemailchimp.update_list_member.assert_called()
        mock_fakemailchimp.update_list_member.assert_any_call(1, subscriber_hash, client_data)
        mock_fakemailchimp.update_list_member.assert_any_call(2, subscriber_hash, client_data)

    @mock.patch.object(res_partner_address.ResPartnerAddress, "archieve_mail_in_list_sync")
    @mock.patch("som_polissa_soci.tests.tests_partner_address.fake_mchimp_client.lists")
    def test_unsubscribe_client_email_in_all_lists(
        self, mock_fakemailchimp, archieve_mail_in_list_sync_mock_function
    ):
        old_email = "test@test.test"

        archieve_mail_in_list_sync_mock_function.return_value = None
        mock_fakemailchimp.get_all_lists.return_value = {
            "lists": [{"id": 1, "name": "som"}, {"id": 2, "name": "som"}]
        }

        partner_address_o = self.pool.get("res.partner.address")
        partner_address_o.unsubscribe_client_email_in_all_lists(
            self.cursor, self.txn, [1], old_email, fake_mchimp_client
        )

        archieve_mail_in_list_sync_mock_function.assert_called()

    @mock.patch.object(res_partner_address.ResPartnerAddress, "read")
    @mock.patch("som_polissa_soci.models.res_partner_address.md5")
    @mock.patch("som_polissa_soci.tests.tests_partner_address.fake_mchimp_client.lists")
    def test_archieve_mail_in_list_sync(
        self, mock_fakemailchimp, mock_md5, res_partner_address_read_mock_function
    ):
        subscriber_hash = "12345"
        email = "test@test.test"
        mock_md5.return_value = FakeMD5(subscriber_hash)
        res_partner_address_read_mock_function.return_value = [{"email": email}]

        partner_address_o = self.pool.get("res.partner.address")
        partner_address_o.archieve_mail_in_list_sync(
            self.cursor, self.txn, [1], 1, fake_mchimp_client
        )

        mock_fakemailchimp.delete_list_member.assert_called()
