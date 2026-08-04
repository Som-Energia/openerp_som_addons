# -*- coding: utf-8 -*-
from mock import mock
from destral import testing
from datetime import date


class SomStashBaseTests(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(SomStashBaseTests, self).setUp()
        self.wizard = self.pool.get('wizard.som.stasher')
        self.imd_obj = self.pool.get('ir.model.data')
        self.ss_obj = self.pool.get('somenergia.soci')
        self.gp_obj = self.pool.get('giscedata.polissa')
        self.rp_obj = self.pool.get('res.partner')
        self.obj_sss = self.pool.get('som.stash.setting')
        self.im_obj = self.pool.get('ir.model')
        self.imf_obj = self.pool.get('ir.model.fields')

    def test_get_partners_inactive_pol_before_datelimit(self):
        date_limit = date(2023, 1, 1)

        res = self.wizard.get_partners_inactive_pol_before_datelimit(
            self.cursor, self.uid, date_limit)

        self.assertEqual(res, [])

        # Com que no tenim cap partner que compleixi les condicions, agafem un que tenim i el
        # modifiquem per a que compleixi les condicions d'estar inactiu abans de la data_limit
        member_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_stash', 'soci_partner_per_fer_stash'
        )[1]
        self.ss_obj.write(self.cursor, self.uid, [member_id], {
                          'baixa': True, 'data_baixa_soci': '2024-01-01'})
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_polissa', 'polissa_domestica_0100'
        )[1]
        partner_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_stash', 'partner_per_fer_stash'
        )[1]
        self.gp_obj.write(self.cursor, self.uid, [pol_id], {
            'state': 'baixa', 'data_baixa': '2020-01-01', 'titular': partner_id})

        res = self.wizard.get_partners_inactive_pol_before_datelimit(
            self.cursor, self.uid, date_limit)

        expected_result = []
        self.assertEqual(res, expected_result)

    @mock.patch('som_stash.wizard.wizard_som_stasher.WizardSomStasher.get_partners_inactive_pol_before_datelimit')  # noqa: E501
    @mock.patch('som_stash.wizard.wizard_som_stasher.WizardSomStasher.get_partners_inactive_soci_before_datelimit')  # noqa: E501
    def test_get_partners_origin_to_stash(self, mock_inactive_pol, mock_inactive_soci):
        years_ago = 6
        partner_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_stash', 'partner_per_fer_stash'
        )[1]
        mock_inactive_pol.return_value = [{
            'date_expiry': '2020-01-01', 'partner_id': partner_id,
        }
        ]
        mock_inactive_soci.return_value = [
        ]

        res = self.wizard.get_partners_origin_to_stash(self.cursor, self.uid, years_ago)

        expected_res = {
            partner_id: {'partner_id': partner_id, 'date_expiry': '2020-01-01'},
        }
        self.assertEqual(res, expected_res)

    def test_get_o2m_models_to_stash(self):

        res = self.wizard.get_o2m_models_to_stash(self.cursor, self.uid)

        expected_res = []
        self.assertEqual(res, expected_res)

        phone_id = self.imf_obj.search(
            self.cursor, self.uid, [
                ('model', '=', 'res.partner.address'), ('name', '=', 'phone')])[0]
        model_id = self.im_obj.search(
            self.cursor, self.uid, [('model', '=', 'res.partner.address')])[0]
        expected_res = [(u'res.partner.address', u'Partner Addresses')]
        self.obj_sss.create(self.cursor, self.uid, {
            'model': model_id,
            'field': phone_id,
            'default_stashed_value': '999666999',
        })

        res = self.wizard.get_o2m_models_to_stash(self.cursor, self.uid)

        self.assertEqual(res, expected_res)
