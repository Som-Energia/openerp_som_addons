
from destral import testing
from destral.transaction import Transaction
import unittest
from osv import fields
import mock
from mock import Mock, ANY

class TestGisceDataCups(testing.OOTestCase):

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.cups_obj = self.openerp.pool.get('giscedata.cups.ps')
        self.contract1_id = self.get_ref('giscedata_polissa', 'polissa_0001')
        self.contract2_id = self.get_ref('giscedata_polissa', 'polissa_autoconsum_03a')
        self.contract3_id = self.get_ref('som_polissa', 'polissa_domestica_0100')

    def tearDown(self):
        self.txn.stop()

    def get_ref(self, module, ref):
        IrModel = self.openerp.pool.get('ir.model.data')
        return IrModel._get_obj(
            self.cursor, self.uid,
            module, ref).id


    @mock.patch('giscedata_cnmc_sips_comer.giscedata_cnmc_sips_comer.fetch_SIPS')
    def test__get_consum_anual_sips_lessThan12(self, mock_function):
        mock_function.return_value = [
            {'fechaFinMesConsumo': '2015-06-17', 'cups': 'ES0031300710578001ZW0F', 'consumoEnergiaActivaEnWhP5': '765000', 'consumoEnergiaActivaEnWhP4': '121000', 'consumoEnergiaActivaEnWhP6': '1524000', 'consumoEnergiaActivaEnWhP1': '324000', 'consumoEnergiaActivaEnWhP3': '3819000', 'consumoEnergiaActivaEnWhP2': '1924000', 'fechaInicioMesConsumo': '2015-05-12'},
            {'fechaFinMesConsumo': '2015-07-13', 'cups': 'ES0031300710578001ZW0F', 'consumoEnergiaActivaEnWhP5': '521000', 'consumoEnergiaActivaEnWhP4': '83000', 'consumoEnergiaActivaEnWhP6': '1212000', 'consumoEnergiaActivaEnWhP1': '172000', 'consumoEnergiaActivaEnWhP3': '2715000', 'consumoEnergiaActivaEnWhP2': '1128000', 'fechaInicioMesConsumo': '2015-06-17'}]
        result = self.cups_obj.get_consum_anual_sips(self.cursor, self.uid, self.contract1_id)
        self.assertEqual(result, False)