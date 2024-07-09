# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class AssignmentTests(testing.OOTestCase):
    def setUp(self):
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.Assignement = self.openerp.pool.get('generationkwh.assignment')

    def tearDown(self):
        pass

    def test__get_generationkwh_monthly_use_empty(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            result = self.Assignement.get_generationkwh_monthly_use(cursor, uid, partner_id, '1990-08')
            self.assertEqual(result, {})

    def test__get_generationkwh_monthly_use(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            contract_id = self.IrModelData.get_object_reference(
                cursor, uid, 'giscedata_polissa', 'polissa_0001'
            )[1]
            result = self.Assignement.get_generationkwh_monthly_use(cursor, uid, partner_id, '2016-03')
            self.assertEqual(result[str(contract_id)]['P1'], 1)

    def test__get_generationkwh_yearly_use(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            contract_id = self.IrModelData.get_object_reference(
                cursor, uid, 'giscedata_polissa', 'polissa_0001'
            )[1]
            result = self.Assignement.get_generationkwh_yearly_use(cursor, uid, partner_id, '2016')
            self.assertEqual(result[str(contract_id)]['P1'], 1)

    def test__get_generationkwh_use_contract_data(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            contract_id = self.IrModelData.get_object_reference(
                cursor, uid, 'giscedata_polissa', 'polissa_0001'
            )[1]
            result = self.Assignement.get_generationkwh_yearly_use(cursor, uid, partner_id, '2016')
            self.assertEqual(result[str(contract_id)]['number'], '0001C')
            self.assertIn("carrer inventat", result[str(contract_id)]['address'])
