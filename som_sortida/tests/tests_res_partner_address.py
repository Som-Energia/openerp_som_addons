# -*- coding: utf-8 -*-
import mock
from destral import testing


class TestsPartnerAddress(testing.OOTestCaseWithCursor):

    @mock.patch('som_polissa_soci.models.res_partner_address.ResPartnerAddress.subscribe_mail_in_list_async')  # noqa: E501
    @mock.patch('som_polissa_soci.models.res_partner_address.ResPartnerAddress.get_mailchimp_list_id')  # noqa: E501
    def test__subscribe_polissa_titular_in_ctss_lists__ok(self, mocked_subscribe, mocked_get_mailchimp_list_id):  # noqa: E501
        cursor = self.cursor
        uid = self.uid
        rpa_obj = self.openerp.pool.get("res.partner.address")
        self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        rpa_obj.subscribe_polissa_titular_in_ctss_lists(cursor, uid, polissa_id)

        mocked_subscribe.assert_called_once()
        mocked_get_mailchimp_list_id.assert_called_once()

    def test__get_polissa_data__ok(self):
        cursor = self.cursor
        uid = self.uid
        rpa_obj = self.openerp.pool.get("res.partner.address")
        self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        res = rpa_obj._get_polissa_data(cursor, uid, polissa_id)

        self.assertEqual(res, {
            'num_socia': 'S202129',
            'situacio_socia': 'Apadrinada',
            'category_id': [],
        })

    def test__fill_merge_fields_titular_polissa_ctss__ok(self):
        cursor = self.cursor
        uid = self.uid
        rpa_obj = self.openerp.pool.get("res.partner.address")
        self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        res = rpa_obj.fill_merge_fields_titular_polissa_ctss(cursor, uid, polissa_id)

        self.maxDiff = None
        self.assertEqual(res, {
            'email_address': u'test@test.test',
            'merge_fields': {
                'EMAIL': u'test@test.test',
                'FNAME': u'Pere',
                'MMERGE11': u'08600',
                'MMERGE3': '',
                'MMERGE4': 'Origen vinculat al CT sense socia',
                'MMERGE5': u'S202129',
                'MMERGE6': 'Apadrinada',
                'MMERGE10': u'Catalu\xf1a',
                'MMERGE6': 'Apadrinada',
                'MMERGE7': u'Berga',
                'MMERGE8': u'Bergued\xe0',
                'MMERGE9': u'Barcelona'
            },
            'status': 'subscribed'
        })

    @mock.patch('som_polissa_soci.models.res_partner_address.ResPartnerAddress.archieve_mail_in_list_sync')  # noqa: E501
    @mock.patch('som_polissa_soci.models.res_partner_address.ResPartnerAddress.get_mailchimp_list_id')  # noqa: E501
    @mock.patch('som_polissa_soci.models.res_partner_address.ResPartnerAddress._get_mailchimp_client')  # noqa: E501
    def test__unsubscribe_titular_in_ctss_lists__uses_address_id(
        self, mocked_get_mailchimp_client, mocked_get_mailchimp_list_id, mocked_archive
    ):
        cursor = self.cursor
        uid = self.uid
        rpa_obj = self.openerp.pool.get("res.partner.address")
        imd_obj = self.openerp.pool.get('ir.model.data')
        address_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'res_partner_address_soci'
        )[1]
        partner_id = rpa_obj.read(cursor, uid, address_id, ['partner_id'])['partner_id'][0]
        mailchimp_client = mock.Mock()

        mocked_get_mailchimp_client.return_value = mailchimp_client
        mocked_get_mailchimp_list_id.return_value = 77

        rpa_obj.unsubscribe_titular_in_ctss_lists(cursor, uid, partner_id)

        mocked_archive.assert_called_once_with(
            cursor, uid, address_id, 77, mailchimp_client
        )
