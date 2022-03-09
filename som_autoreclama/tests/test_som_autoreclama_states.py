# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from expects import *
from datetime import date
import mock
from .. import giscedata_atc, som_autoreclama_state_history

class SomAutoreclamaStatesTest(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def test_first_state_correct_dummy(self):
        imd_obj = self.get_model('ir.model.data')
        correct_state_id = imd_obj.get_object_reference(
                self.cursor, self.uid, 'som_autoreclama', 'correct_state_workflow_atc'
        )[1]
        sas_obj = self.get_model('som.autoreclama.state')
        first = sas_obj.browse(self.cursor, self.uid, correct_state_id)
        self.assertEqual(first.name, 'Correcte')

    @mock.patch.object(som_autoreclama_state_history.SomAutoreclamaStateHistoryAtc, "create")
    @mock.patch.object(giscedata_atc.GiscedataAtc, "create")
    def test_create_atc__state_correct_in_history(self, mock_create_atc, mock_create_history):
        sash_obj = self.get_model('som.autoreclama.state.history.atc')
        mock_create_atc.return_value = 1

        def create_history_mock(cursor, uid, id, vals):
            return {}

        mock_create_history.side_effect = create_history_mock

        atc_obj = self.get_model('giscedata.atc')
        atc_obj.create(self.cursor, self.uid, {})

        vals = {
            'atc_id': 1,
            'autoreclama_state_id':1,
            'change_date': date.today().strftime("%d-%m-%Y")
        }
        sash_obj.create.assert_called_once_with(self.cursor, self.uid, vals)
