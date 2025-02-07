# -*- coding: utf-8 -*-
from destral.testing import OOTestCaseWithCursor


class TestsFacturesUnpaymentExpenses(OOTestCaseWithCursor):
    def setUp(self):
        super(TestsFacturesUnpaymentExpenses, self).setUp()
        self.fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        self.imd_obj = self.openerp.pool.get("ir.model.data")

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

    def test_check_total_invoice_more_than_unpaymnet_expenses(self):
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
