# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv.osv import except_osv
from destral.transaction import Transaction
import mock
from giscedata_switching_comer.tests import TestWizardValidateD101

from .. import wizard

class TestWizardValidateD101(TestWizardValidateD101):

    def test__create_step_d1_02_motiu_06__accept_done(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            sw_obj = self.openerp.pool.get('giscedata.switching')
            d101_obj = self.openerp.pool.get('giscedata.switching.d1.01')
            d102_obj = self.openerp.pool.get('giscedata.switching.d1.02')
            wiz_validate_obj = self.openerp.pool.get('wizard.validate.d101')

            d1_id = self.create_d1_case_at_step_01(txn)

            sw = sw_obj.browse(cursor, uid, d1_id)
            pas_id = sw.step_ids[0].pas_id
            id_pas = int(pas_id.split(',')[1])
            d101_obj.write(cursor, uid, [id_pas], {'motiu_canvi': '06'})

            wiz_init = {
                'sw_id': d1_id
            }
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)

            wiz.validate_d101_autoconsum()

            d102_id = wiz.read(['generated_d102'])[0]['generated_d102']

            sw_id = d102_obj.read(cursor, uid, d102_id, ['sw_id'])['sw_id'][0]
            sw_obj.write(cursor, uid, sw_id, {"state": "done"})
            
            d102 = d102_obj.browse(cursor,uid, d102_id)

            self.assertEqual(d102.sw_id.id, d1_id)
            self.assertEqual(d102.sw_id.state, 'done')

    def test__create_case_m1_01_motiu_06__S_R(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            m101_obj = self.openerp.pool.get('giscedata.switching.m1.01')

            pol_id = self.get_contract_id(txn)

            #wizard to test
            sw_obj = self.openerp.pool.get('giscedata.switching')
            d101_obj = self.openerp.pool.get('giscedata.switching.d1.01')
            d102_obj = self.openerp.pool.get('giscedata.switching.d1.02')
            wiz_validate_obj = self.openerp.pool.get('wizard.validate.d101')

            d1_id = self.create_d1_case_at_step_01(txn)

            sw = sw_obj.browse(cursor, uid, d1_id)
            pas_id = sw.step_ids[0].pas_id
            id_pas = int(pas_id.split(',')[1])
            d101_obj.write(cursor, uid, [id_pas], {'motiu_canvi': '06'})

            wiz_init = {
                'sw_id': d1_id
            }
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)
            
            wiz.validate_d101_autoconsum()

            m1_id = wiz.read(['generated_m1'])[0]['generated_m1']

            m1 = sw_obj.browse(cursor, uid, m1_id)

            self.assertEqual(m1.state, 'draft')
            self.assertEqual(len(m1.step_ids), 1)
            self.assertEqual(m1.polissa_ref_id.id, pol_id)
            self.assertEqual(m1.additional_info[0:48], '(S)[R] Mod. Acord repartiment/fitxer coeficients')
            id_pas = int(m1.step_ids[0].pas_id.split(',')[1])
            pas = m101_obj.browse(cursor, uid, id_pas)
            self.assertEqual(pas.sollicitudadm, 'S')
            self.assertEqual(pas.canvi_titular, 'R')
