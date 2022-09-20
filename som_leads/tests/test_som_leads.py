# -*- coding: utf-8 -*-
from destral import testing
import unittest
from destral.transaction import Transaction

from expects import *
import osv

import csv
import os
import mock


class SomLeadsTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.imd_obj = self.openerp.pool.get('ir.model.data')
        self.leads_obj = self.openerp.pool.get('som.soci.crm.lead')
        self.partner_obj = self.openerp.pool.get('res.partner')
        self.address_obj = self.openerp.pool.get('res.partner.address')
        self.soci_obj = self.openerp.pool.get('somenergia.soci')
        self.emission_obj = self.openerp.pool.get('generationkwh.emission')
        self.investment_obj = self.openerp.pool.get('generationkwh.investment')
        self.invoice_obj = self.openerp.pool.get('account.invoice')

        self.apoobl_emission_id = self.emission_obj.search(self.cursor, self.uid,
            [('code','=', 'APO_OB')])[0]

    def tearDown(self):
        self.txn.stop()

    @mock.patch("som_leads.som_soci_crm_lead.SomSociCrmLead.create_entities")
    def test__create_entities(self, mocked_func):
        imd_obj = self.openerp.pool.get('ir.model.data')
        leads_obj = self.openerp.pool.get('som.soci.crm.lead')
        lead_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]

        res = leads_obj.stage_next(self.cursor, self.uid, [lead_id])
        self.assertTrue(res)
        mocked_func.assert_called_with(self.cursor, self.uid, [lead_id], None)

    def test__create_entities__ok(self):

        lead_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        lead_info = self.leads_obj.read(self.cursor, self.uid, lead_id)
        partner_search_params = [
            ('name', '=', lead_info['partner_nom']),
            ('vat','=', lead_info['partner_vat'])
        ]
        address_search_params = [('name', '=', lead_info['partner_nom'])]
        partner_pre_result = self.partner_obj.search(self.cursor, self.uid, partner_search_params)
        address_pre_result = self.address_obj.search(self.cursor, self.uid, address_search_params)
        self.assertEqual(partner_pre_result, [])
        self.assertEqual(address_pre_result, [])

        res = self.leads_obj.create_entities(self.cursor, self.uid, lead_id)

        self.assertTrue(res)

        lead = self.leads_obj.browse(self.cursor, self.uid, lead_id)

        # Create partner
        partner_post_result = self.partner_obj.search(self.cursor, self.uid, partner_search_params)
        address_post_result = self.address_obj.search(self.cursor, self.uid, address_search_params)
        self.assertTrue(partner_post_result, [lead.partner_id.id])
        self.assertTrue(address_post_result, [lead.partner_address_id.id])

        # Create soci
        soci_id = self.soci_obj.search(self.cursor, self.uid, [('partner_id', '=', lead.partner_id.id)])[0]
        self.assertEqual(soci_id, lead.soci_id.id)

        # Create APO
        apo_id = self.investment_obj.search(self.cursor, self.uid, [('member_id','=', lead.soci_id.id)])[0]
        apo = self.investment_obj.browse(self.cursor, self.uid, apo_id)
        self.assertEqual(apo_id, lead.investment_id.id)
        self.assertFalse(apo.draft)
        self.assertTrue(apo.nshares, 1)

        # Create invoice
        inv_id = self.invoice_obj.search(self.cursor, self.uid, [
            ('partner_id', '=', lead.partner_id.id), ('origin', '=', apo.name), ('state','=', 'draft')
        ])
        self.assertTrue(inv_id)