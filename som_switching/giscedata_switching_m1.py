# -*- coding: utf-8 -*-
from osv import osv


class GiscedataSwitchingM1_01(osv.osv):

    _name = "giscedata.switching.m1.01"
    _inherit = "giscedata.switching.m1.01"

    def config_step(self, cursor, uid, ids, vals, context=None):
        new_contract_values = vals.get("new_contract_values")
        if new_contract_values:
            new_contract_values.update(
                {
                    "category_id": [(6, 0, [])],
                }
            )
            titular_id = new_contract_values.get('titular')
            if titular_id:
                imd_obj = self.pool.get("ir.model.data")
                partner_obj = self.pool.get("res.partner")
                vat = partner_obj.read(cursor, uid, titular_id, ['vat'])['vat']
                if partner_obj.is_enterprise_vat(vat):
                    default_process = imd_obj.get_object_reference(
                        cursor, uid, "account_invoice_pending", "default_pending_state_process"
                    )[1]
                    new_contract_values.update({"process_id": default_process})
                else:
                    bo_social_process = imd_obj.get_object_reference(
                        cursor, uid, 'giscedata_facturacio_comer_bono_social',
                        'bono_social_pending_state_process'
                    )[1]
                    new_contract_values.update({"process_id": bo_social_process})

        res = super(GiscedataSwitchingM1_01, self).config_step(cursor, uid, ids, vals, context)
        return res


GiscedataSwitchingM1_01()
