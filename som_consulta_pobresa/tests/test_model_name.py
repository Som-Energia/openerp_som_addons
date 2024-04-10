# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestModelName(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_something(self):
        """First line of docstring appears in test logs.
        Other lines do not.
        Any method starting with ``test_`` will be tested.
        """
        cursor = self.cursor
        uid = self.uid
        self.openerp.pool.get('res.users')
        imd_obj = self.openerp.pool.get('ir.model.data')
        reg_id = imd_obj.get_object_reference(
            cursor, uid,
            'som_template', 'som_template_user_editable_record'
        )[1]
        print reg_id
        self.assertEqual(True, True)
