# -*- coding: utf-8 -*-
import unittest
from destral import testing
from destral.transaction import Transaction

class powersms_tests(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get('ir.model.data')

    def tearDown(self):
        pass

    def test__dummyTest(self):
        self.assertTrue(True)

    def test__powersms_send_wizard__save_to_smsbox(self):
        """
        Checks if when state changed, everithing works
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.openerp.pool.get('powersms.send.wizard')
            temp_id = self.imd_obj.get_object_reference(
                cursor, uid, 'powersms', 'sms_template_001')[1]
            rpa_id = self.imd_obj.get_object_reference(
                cursor, uid, 'base', 'res_partner_address_c2c_1')[1]
            pca_id = self.imd_obj.get_object_reference(
                cursor, uid, 'powersms', 'sms_account_001')[1]
            vals = {'account': pca_id, 'body_text': 'Test text'}
            context = {'template_id': temp_id, 'rel_model': 'res_partner_address', 'src_rec_ids':[rpa_id],
            'active_id': rpa_id, 'active_ids': [rpa_id], 'src_model': 'res.partner.address','from': 'Som Energia',
            'account': pca_id}

            wizard_id = model.create(cursor, uid, vals, context)
            wizard_load_n = model.browse(cursor, uid, wizard_id)
            sms_created_id = wizard_load_n.save_to_smsbox(context)

            psb = self.openerp.pool.get('powersms.smsbox')
            sms_id = psb.search(cursor, uid,
                [('id','=',sms_created_id), ('psms_body_text', '=', 'Test text'), ('folder','=','outbox')]
            )
            self.assertTrue(sms_created_id[0] in sms_id)

    def test__powersms_send_wizard__send_sms_isNotValid(self):
        """
        Checks if when state changed, everithing works
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.openerp.pool.get('powersms.send.wizard')
            temp_id = self.imd_obj.get_object_reference(
                cursor, uid, 'powersms', 'sms_template_001')[1]
            rpa_id = self.imd_obj.get_object_reference(
                cursor, uid, 'base', 'res_partner_address_c2c_1')[1]
            pca_id = self.imd_obj.get_object_reference(
                cursor, uid, 'powersms', 'sms_account_001')[1]
            vals = {'account': pca_id, 'body_text': 'Test sms in draft folder'}
            context = {'template_id': temp_id, 'rel_model': 'res_partner_address', 'src_rec_ids':[rpa_id],
            'active_id': rpa_id, 'active_ids': [rpa_id], 'src_model': 'res.partner.address','from': 'Som Energia',
            'account': pca_id}

            wizard_id = model.create(cursor, uid, vals, context)
            wizard_load_n = model.browse(cursor, uid, wizard_id)
            wizard_load_n.send_sms(context)

            psb = self.openerp.pool.get('powersms.smsbox')
            sms_id = psb.search(cursor, uid,
                [('psms_body_text', '=', 'Test sms in draft folder'), ('folder','=','drafts')]
            )
            self.assertTrue(sms_id)
