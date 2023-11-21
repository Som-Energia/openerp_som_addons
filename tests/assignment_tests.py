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
            assignment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'assignment_0001'
            )[1]
            result = self.Assignement.get_generationkwh_monthly_use(cursor, uid, [assignment_id], '1990-08')
            self.assertEqual(result, {str(assignment_id): {}})

    def test__get_generationkwh_monthly_use(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            assignment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'assignment_0001'
            )[1]
            result = self.Assignement.get_generationkwh_monthly_use(cursor, uid, [assignment_id], '2016-03')
            self.assertEqual(result[str(assignment_id)]['P1'], 1)

    def test__get_generationkwh_yearly_use(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            assignment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'assignment_0001'
            )[1]
            result = self.Assignement.get_generationkwh_yearly_use(cursor, uid, [assignment_id], '2016')
            self.assertEqual(result[str(assignment_id)]['P1'], 1)
