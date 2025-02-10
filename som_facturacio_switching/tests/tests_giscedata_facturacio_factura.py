# -*- coding: utf-8 -*-
from destral.testing import OOTestCaseWithCursor


class TestsFacturesUnpaymentExpenses(OOTestCaseWithCursor):
    def setUp(self):
        super(TestsFacturesUnpaymentExpenses, self).setUp()
        self.fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.extra_obj = self.openerp.pool.get('giscedata.facturacio.extra')

    def test_check_pobresa_energetica(self):
        """ComOOTestCaseWithCursorprovem que no té pobresa energètica abans de crear l'extra line"""
        cursor, uid = self.cursor, self.uid
        # Prepare data

        fact_id = self.imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]

        # Test
        res = self.fact_obj.check_pobresa_energetica(cursor, uid, [fact_id])

        # Assert
        self.assertEqual(res, False)

    def test__check_total_invoice_more_than_unpaymnet_expenses__less_amount(self):
        """Comprovem que la factura no té un import total inferior a l'import de l'extra line"""
        cursor, uid = self.cursor, self.uid
        # Prepare data
        fact_id = self.imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]

        # Test
        res = self.fact_obj.check_total_invoice_more_than_unpaymnet_expenses(
            cursor, uid, [fact_id]
        )

        # Assert
        self.assertEqual(res, False)

    def test__check_total_invoice_more_than_unpaymnet_expenses__more_amount(self):
        """Comprovem que la factura té un import total inferior a l'import de l'extra line"""
        cursor, uid = self.cursor, self.uid
        # Prepare data
        fact_id = self.imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]
        extra_id = self.imd_obj.get_object_reference(
            cursor, uid, "som_facturacio_switching", "extra_line_1"
        )[1]
        self.extra_obj.write(cursor, uid, [extra_id], {"quantity": 28})

        # Test
        res = self.fact_obj.check_total_invoice_more_than_unpaymnet_expenses(
            cursor, uid, [fact_id]
        )

        # Assert
        self.assertEqual(res, True)
