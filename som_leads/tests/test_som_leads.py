# -*- coding: utf-8 -*-
from destral import testing
import unittest
from destral.transaction import Transaction

from expects import *
import osv

import csv
import os
import mock

from ..exceptions.leads_exceptions import (
    InvalidLeadState,
    InvalidParameters,
    MissingMandatoryFields,
    MemberExists,
    )

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
    def test__create_entities__isCalled(self, mocked_func):
        imd_obj = self.openerp.pool.get('ir.model.data')
        leads_obj = self.openerp.pool.get('som.soci.crm.lead')
        lead_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        leads_obj.write(self.cursor, self.uid, [lead_id], {'state':'open', 'stage_id':1})
        res = leads_obj.stage_next(self.cursor, self.uid, [lead_id])
        self.assertTrue(res)
        mocked_func.assert_called_with(self.cursor, self.uid, [lead_id], None)

    def test__stage_next__exception(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        leads_obj = self.openerp.pool.get('som.soci.crm.lead')
        lead_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        leads_obj.write(self.cursor, self.uid, [lead_id], {'state':'draft'})
        with self.assertRaises(InvalidLeadState) as ctx:
            leads_obj.stage_next(self.cursor, self.uid, [lead_id])
        self.assertEqual(ctx.exception.to_dict()['error'],
            'El lead amb ID: 1 no està en estat obert'
        )

    def test__create_entities__ok(self):

        lead_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        self.leads_obj.write(self.cursor, self.uid, [lead_id],
            {
                'partner_nom': 'newmember',
                'partner_vat': 'ESY5871952C'
            }
        )

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
        self.assertEqual(partner_post_result, [lead.partner_id.id])
        self.assertEqual(address_post_result, [lead.partner_address_id.id])

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

    def default_vals(self, removed=[], **kwds):
        vals = dict(
            partner_vat = 'ESY5871952C',
            is_juridic=True,
            partner_nom="myname",
            address_phone="652385827",
            address_mobile="652385828",
            address_email="my.email@test.com",
            address_zip="17003",
            address_state_id=20,
            address_nv="mystreet, 10",
            address_municipi_id=2524,
            partner_lang="en_US",
            payment_method="RECIBO_CSB",
            iban="ES2320383592502299212874",
            name="myname",
        )
        vals.update(**kwds)
        for k in removed:
            del vals[k]
        return vals

    def test__create_new_member__whenInvalidParameters(self):
        vals = self.default_vals(
            partner_vat='badnif',
        )
        with self.assertRaises(InvalidParameters) as ctx:
            self.leads_obj.create_new_member(self.cursor, self.uid, vals)
        self.assertEqual(ctx.exception.to_dict()['error'],
            'Invalid values for parameters partner_vat'
        )

    def test__create_new_member__whenRemoveAddressZip(self):
        vals = self.default_vals(
            removed=['address_zip']
        )
        with self.assertRaises(MissingMandatoryFields) as ctx:
            self.leads_obj.create_new_member(self.cursor, self.uid, vals)
        self.assertEqual(ctx.exception.to_dict()['error'],
            u"Es deuen completar els següents camps 'address_zip'."
        )

    def test__create_new_member__whenCreatePartner(self):
        result = self.leads_obj.create_new_member(self.cursor, self.uid, self.default_vals())

        lead = self.leads_obj.browse(self.cursor, self.uid, result['lead_id'])

        partner_search_params = [
            ('name', '=', lead['partner_nom']),
            ('vat','=', lead['partner_vat'])
        ]
        address_search_params = [('name', '=', lead['partner_nom'])]

        partner_id = self.partner_obj.search(self.cursor, self.uid, partner_search_params)[0]
        address_id = self.address_obj.search(self.cursor, self.uid, address_search_params)[0]
        self.assertEqual(partner_id, lead.partner_id.id)
        self.assertEqual(address_id, lead.partner_address_id.id)

        partner = self.partner_obj.browse(self.cursor, self.uid, partner_id)
        self.assertEqual(partner['name'], "myname")
        self.assertEqual(partner['lang'], 'en_US')

        address = self.address_obj.browse(self.cursor, self.uid, address_id)
        self.assertEqual(address['phone'], "652385827")
        self.assertEqual(address['mobile'], "652385828")
        self.assertEqual(address['email'], "my.email@test.com")
        self.assertEqual(address['state_id'].id, 20)
        self.assertEqual(address['zip'], "17003")
        self.assertEqual(address['street'], "mystreet, 10")
        self.assertEqual(address['id_municipi'].id, 2524)

    def test__create_new_member__whenCreateSoci(self):
        result = self.leads_obj.create_new_member(self.cursor, self.uid, self.default_vals())

        lead = self.leads_obj.browse(self.cursor, self.uid, result['lead_id'])

        soci_id = self.soci_obj.search(self.cursor, self.uid, [('partner_id', '=', lead.partner_id.id)])[0]
        self.assertEqual(soci_id, lead.soci_id.id)

        soci = self.soci_obj.browse(self.cursor, self.uid, soci_id)
        self.assertFalse(soci['baixa'])

    def test__create_new_member__whenCreateAPO(self):
        result = self.leads_obj.create_new_member(self.cursor, self.uid, self.default_vals())

        lead = self.leads_obj.browse(self.cursor, self.uid, result['lead_id'])

        apo_id = self.investment_obj.search(self.cursor, self.uid, [('member_id','=', lead.soci_id.id)])[0]
        apo = self.investment_obj.browse(self.cursor, self.uid, apo_id)
        self.assertEqual(apo_id, lead.investment_id.id)
        self.assertFalse(apo.draft)
        self.assertEqual(apo.nshares, 1)

    def test__create_new_member__whenCreateInvoice(self):
        result = self.leads_obj.create_new_member(self.cursor, self.uid, self.default_vals())

        lead = self.leads_obj.browse(self.cursor, self.uid, result['lead_id'])

        apo_id = self.investment_obj.search(self.cursor, self.uid, [('member_id','=', lead.soci_id.id)])[0]
        apo = self.investment_obj.browse(self.cursor, self.uid, apo_id)
        inv_id = self.invoice_obj.search(self.cursor, self.uid, [
            ('partner_id', '=', lead.partner_id.id), ('origin', '=', apo.name), ('state','=', 'open')
        ])
        self.assertTrue(inv_id)

    def test__create_new_member__whenSociExists(self):
        vals = self.default_vals(
            partner_vat='ES17419856R',
        )
        with self.assertRaises(MemberExists) as ctx:
            self.leads_obj.create_new_member(self.cursor, self.uid, vals)
        exception_vals = ctx.exception.to_dict()
        self.assertEqual(exception_vals['error'],
            u"S'ha trobat un soci amb el partner_id {} i està actiu.".format(exception_vals['partner_id'])
        )

    @mock.patch("som_leads.som_soci_crm_lead.SomSociCrmLead.create_entities")
    def test__on_exit_filled_form__create_entities_is_called(self, mocked_func):
        a_valid_stage_name = 'Formulari omplert'
        a_valid_open_state = 'open'
        self.cls_obj = self.openerp.pool.get('crm.case.stage')
        crm_lead_stage_id = self.cls_obj.search(self.cursor, self.uid, [('name','=', a_valid_stage_name)])[0]
        lead_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        self.leads_obj.write(self.cursor, self.uid, [lead_id],
            {
                'stage_id': crm_lead_stage_id,
                'state': a_valid_open_state
            }
        )

        self.leads_obj.on_exit_filled_form(self.cursor, self.uid, [lead_id])

        mocked_func.assert_called_with(self.cursor, self.uid, [lead_id], {})

    @mock.patch("som_leads.som_soci_crm_lead.SomSociCrmLead.create_entities")
    def test__on_exit_filled_form__create_entities_is_not_called(self, mocked_func):
        an_invalid_stage_name = 'Remesat'
        a_valid_open_state = 'open'
        self.cls_obj = self.openerp.pool.get('crm.case.stage')
        crm_lead_stage_id = self.cls_obj.search(self.cursor, self.uid, [('name','=', an_invalid_stage_name)])[0]
        lead_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        self.leads_obj.write(self.cursor, self.uid, [lead_id],
            {
                'stage_id': crm_lead_stage_id,
                'state': a_valid_open_state
            }
        )

        self.leads_obj.on_exit_filled_form(self.cursor, self.uid, [lead_id])

        mocked_func.assert_not_called()

    @mock.patch("som_leads.som_soci_crm_lead.SomSociCrmLead.add_invoice_payment_order")
    def test__on_exit_proces_en_curs__add_invoice_payment_order_is_called(self, mocked_func):
        a_valid_stage_name = 'Procés en curs'
        a_valid_open_state = 'open'
        self.cls_obj = self.openerp.pool.get('crm.case.stage')
        crm_lead_stage_id = self.cls_obj.search(self.cursor, self.uid, [('name','=', a_valid_stage_name)])[0]
        lead_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        self.leads_obj.write(self.cursor, self.uid, [lead_id],
            {
                'stage_id': crm_lead_stage_id,
                'state': a_valid_open_state
            }
        )

        self.leads_obj.on_exit_proces_en_curs(self.cursor, self.uid, [lead_id])

        mocked_func.assert_called_with(self.cursor, self.uid, [lead_id], {})

    @mock.patch("som_leads.som_soci_crm_lead.SomSociCrmLead.add_invoice_payment_order")
    def test__on_exit_proces_en_curs__add_invoice_payment_order_is_not_called(self, mocked_func):
        an_invalid_stage_name = 'Procés en curs TPV'
        a_valid_open_state = 'open'
        self.cls_obj = self.openerp.pool.get('crm.case.stage')
        crm_lead_stage_id = self.cls_obj.search(self.cursor, self.uid, [('name','=', an_invalid_stage_name)])[0]

        lead_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_leads', 'som_leads_alta_socia1')[1]
        self.leads_obj.write(self.cursor, self.uid, [lead_id],
            {
                'stage_id': crm_lead_stage_id,
                'state': a_valid_open_state
            }
        )

        self.leads_obj.on_exit_proces_en_curs(self.cursor, self.uid, [lead_id])

        mocked_func.assert_not_called()

    @mock.patch("som_leads.som_soci_crm_lead.SomSociCrmLead.add_invoice_payment_order")
    @mock.patch("som_leads.som_soci_crm_lead.SomSociCrmLead.create_entities")
    def test__create_new_member__calls_required_stages(self, mock_create_entites, mock_add_invoice_payment_order):
        result = self.leads_obj.create_new_member(self.cursor, self.uid, self.default_vals())
        expected_lead_id = result['lead_id']
        mock_create_entites.assert_called_with(self.cursor, self.uid, [expected_lead_id], {})
        mock_add_invoice_payment_order.assert_called_with(self.cursor, self.uid, [expected_lead_id], {})
