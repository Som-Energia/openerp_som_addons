# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import mock
import mailchimp_marketing


class SomenergiaSociTests(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.IrModelData = self.openerp.pool.get("ir.model.data")
        self.ResPartner = self.openerp.pool.get("res.partner")
        self.ResPartnerAddress = self.openerp.pool.get("res.partner.address")
        self.Polissa = self.openerp.pool.get("giscedata.polissa")
        self.Soci = self.openerp.pool.get("somenergia.soci")

    def tearDown(self):
        self.txn.stop()

    @mock.patch(
        "som_polissa_soci.models.res_partner_address.ResPartnerAddress.archieve_mail_in_list")
    @mock.patch(
        "som_polissa_soci.models.res_partner_address.ResPartnerAddress.get_mailchimp_list_id")
    @mock.patch.object(mailchimp_marketing, "Client")
    def test__arxiva_client_mailchimp__withAddress(
        self, mock_mailchimp_client, mock_get_list_id, mock_archieve
    ):

        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_nosoci1"
        )[1]
        address_list = self.ResPartner.read(self.cursor, self.uid, partner_id, ["address"])[
            "address"
        ]

        mock_get_list_id.return_value = "id"
        mock_mailchimp_client.return_value = "MAILCHIMP_CLIENT"

        self.ResPartner.arxiva_client_mailchimp(self.cursor, self.uid, partner_id)

        mock_archieve.assert_called_with(
            self.cursor, self.uid, address_list, "id", "MAILCHIMP_CLIENT"
        )

    @mock.patch(
        "som_polissa_soci.models.res_partner_address.ResPartnerAddress.archieve_mail_in_list"
    )
    @mock.patch(
        "som_polissa_soci.models.res_partner_address.ResPartnerAddress.get_mailchimp_list_id"
    )
    @mock.patch.object(mailchimp_marketing, "Client")
    def test__arxiva_client_mailchimp__withManyAddress(
        self, mock_mailchimp_client, mock_get_list_id, mock_archieve
    ):
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_nosoci2"
        )[1]
        address_list = self.ResPartner.read(self.cursor, self.uid, partner_id, ["address"])[
            "address"
        ]

        mock_get_list_id.return_value = "id"
        mock_mailchimp_client.return_value = "MAILCHIMP_CLIENT"

        self.ResPartner.arxiva_client_mailchimp(self.cursor, self.uid, partner_id)

        mock_archieve.assert_called_with(
            self.cursor, self.uid, sorted(address_list), "id", "MAILCHIMP_CLIENT"
        )

    @mock.patch(
        "som_polissa_soci.models.res_partner_address.ResPartnerAddress.archieve_mail_in_list"
    )
    @mock.patch(
        "som_polissa_soci.models.res_partner_address.ResPartnerAddress.get_mailchimp_list_id"
    )
    @mock.patch.object(mailchimp_marketing, "Client")
    def test__arxiva_client_mailchimp__isMember(
        self, mock_mailchimp_client, mock_get_list_id, mock_archieve
    ):

        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_soci"
        )[1]
        mock_get_list_id.return_value = "id"
        mock_mailchimp_client.return_value = "MAILCHIMP_CLIENT"

        self.ResPartner.arxiva_client_mailchimp(self.cursor, self.uid, partner_id)

        mock_archieve.assert_not_called()
