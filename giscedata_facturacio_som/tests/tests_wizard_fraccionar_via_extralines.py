# -*- coding: utf-8 -*-
from destral import testing
import mock


class TestWizardFraccionarViaExtralines(testing.OOTestCaseWithCursor):
    def load_models(self, cursor, uid):
        self.fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        self.wiz_obj = self.openerp.pool.get("wizard.fraccionar.via.extralines")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.factura_id = self.imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]

    @mock.patch(
        "giscedata_facturacio.giscedata_facturacio.GiscedataFacturacioFactura.fraccionar_via_extralines"  # noqa: E501
    )
    def test_action_fraccionar_via_extralines_with_first_term_payment(
        self, fraccionar_via_extraline_mock
    ):
        cursor = self.cursor
        uid = self.uid
        self.load_models(cursor, uid)
        values = {
            "first_term_payment": True,
            "ntermes": 4,
        }
        context = {"active_ids": [self.factura_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, values, context)
        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)
        self.wiz_obj.action_fraccionar_via_extralines(cursor, uid, [wiz_id], context)

        factura = self.fact_obj.browse(cursor, uid, self.factura_id)
        expected_total = (3 / 4.0) * (factura.amount_total)
        fraccionar_via_extraline_mock.assert_called_with(
            mock.ANY,
            mock.ANY,
            factura.id,
            values["ntermes"] - 1,
            wizard.data_inici,
            mock.ANY,
            amount=expected_total,
            context=context,
            journal_id=wizard.journal_id.id,
        )

    @mock.patch(
        "giscedata_facturacio.giscedata_facturacio.GiscedataFacturacioFactura.fraccionar_via_extralines"  # noqa: E501
    )
    def test_action_fraccionar_via_extralines_without_first_term_payment(
        self, fraccionar_via_extraline_mock
    ):
        cursor = self.cursor
        uid = self.uid
        self.load_models(cursor, uid)
        values = {
            "first_term_payment": False,
            "ntermes": 4,
        }
        context = {"active_ids": [self.factura_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, values, context)
        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)
        self.wiz_obj.action_fraccionar_via_extralines(cursor, uid, [wiz_id], context)

        factura = self.fact_obj.browse(cursor, uid, self.factura_id)
        factura.amount_total
        fraccionar_via_extraline_mock.assert_called_with(
            mock.ANY,
            mock.ANY,
            factura.id,
            values["ntermes"],
            wizard.data_inici,
            mock.ANY,
            context=context,
            journal_id=wizard.journal_id.id,
        )
