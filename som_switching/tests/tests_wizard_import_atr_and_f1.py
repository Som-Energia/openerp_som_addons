# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import mock
from datetime import datetime

class TestWizardImportAtrAndF1(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()
    
    @mock.patch('__builtin__.open')
    def test__import_F1__originalName(self, mock_open):        
        wiz_o = self.pool.get('wizard.import.atr.and.f1')
        wiz_content = {'filename': 'nomFitxer'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_content)

        zip_handler = wiz_o._create_tmp_zip(self.cursor, self.uid, [wiz_id], 'testDirectory', 'F1_')

        mock_open.assert_called_with('testDirectory/F1_nomFitxer', 'w+')

    @mock.patch('__builtin__.open')
    def test__import_F1_subfolder__originalName(self, mock_open):
        wiz_o = self.pool.get('wizard.import.atr.and.f1')
        wiz_content = {'filename': '25_07_2022/nomFitxer'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_content)

        zip_handler = wiz_o._create_tmp_zip(self.cursor, self.uid, [wiz_id], 'testDirectory', 'F1_')

        mock_open.assert_called_with('testDirectory/F1_nomFitxer', 'w+')

    @mock.patch('giscedata_switching.wizard.wizard_import_atr_and_f1.datetime')
    @mock.patch('__builtin__.open')
    def test__import_ATR__nameChanged(self, mock_open, mock_datetime):
        wiz_o = self.pool.get('wizard.import.atr.and.f1')
        wiz_content = {'filename': ''}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_content)
        
        today = datetime.strftime(datetime.today(), '%Y%m%d')
        mock_datetime.strftime.return_value = today

        zip_handler = wiz_o._create_tmp_zip(self.cursor, self.uid, wiz_id, 'testDirectory', 'ATR_')

        filename = 'testDirectory/ATR_' + today + '.zip'
        mock_open.assert_called_with(filename, 'w+')
