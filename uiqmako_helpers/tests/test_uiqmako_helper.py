# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestUIQMakoHelper(testing.OOTestCaseWithCursor):
    def test_render_mako_text(self):
        ukm_obj = self.openerp.pool.get("som.uiqmako.helper")
        imd_obj = self.openerp.pool.get("ir.model.data")
        res_obj = self.openerp.pool.get("res.partner")

        partner_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_agrolait"
        )[1]
        partner_name = res_obj.read(self.cursor, self.uid, partner_id, ["name"])["name"]
        mako_text = """
            <html>
            <body>
            Hello ${object.name}!
            </body>
            </html>
        """
        ukm_id = ukm_obj.create(self.cursor, self.uid, {})
        result = ukm_obj.render_mako_text(
            self.cursor, self.uid, ukm_id, mako_text, "res.partner", 3
        )

        self.assertEqual(result, mako_text.replace("${object.name}", partner_name))
