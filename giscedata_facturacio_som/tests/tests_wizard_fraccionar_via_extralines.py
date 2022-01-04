# -*- coding: utf-8 -*-
from destral import testing
from .. import giscedata_facturacio 
import mock

class TestWizardFraccionarViaExtralines(testing.OOTestCaseWithCursor):

    def setUp(self):
        self.fact_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        self.wiz_obj = self.openerp.pool.get('wizard.fraccionar.via.extralines')
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.factura_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0001'
        )[1]

    #@mock.patch("giscedata_facturacio.GiscedataFacturacioFactura.fraccionar_via_extralines")
    @mock.patch.object(giscedata_facturacio.GiscedataFacturacioFactura, 'fraccionar_via_extralines')
    def test_asdasd(self, fraccionar_via_extraline_mock):
        fraccionar_via_extraline_mock.return_value = {}

        fraccionar_via_extraline_mock.assert_called_with('','')
