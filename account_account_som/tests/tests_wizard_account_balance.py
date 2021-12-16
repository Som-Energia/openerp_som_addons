# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

from osv import fields

class TestWizardAccountBalance(testing.OOTestCase):

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_wizard_account_balance_report(self):
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.send.reports')

        wiz_id = wiz_obj.create(cursor, uid, {},context={})
        #wiz_obj.send_reports(cursor, uid, [wiz_id], context={}})
