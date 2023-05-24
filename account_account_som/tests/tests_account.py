# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import xml.etree.ElementTree as ET


class TestAccountAccountSom(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_saveAccount_withParentRequired(self):
        acc_obj = self.openerp.pool.get("account.account")
        imd_obj = self.openerp.pool.get("ir.model.data")

        view_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account_account_som", "view_account_form_som"
        )[1]

        ac1 = acc_obj.browse(self.cursor, self.uid, 2)

        res = acc_obj.fields_view_get(
            self.cursor, self.uid, view_id=view_id, view_type="form", context={"active_id": ac1.id}
        )

        xml = res["arch"]
        el = ET.fromstring(xml)
        field_list = el.find("group").findall("field")
        field_parent = [field for field in field_list if field.attrib["name"] == "parent_id"]
        dictionary = field_parent[0].attrib

        assert "required" in dictionary and dictionary["required"] == "True"

        # print res['arch']
        # assert '<field name="parent_id" required="True"/>' in res['arch']
