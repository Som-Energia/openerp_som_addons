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

        res = super(GiscedataSwitchingM1_01, self).config_step(cursor, uid, ids, vals, context)

        if new_contract_values:
            titular_id = new_contract_values.get('titular')
            if titular_id:
                m1 = self.browse(cursor, uid, ids, context=context)
                new_polissa_id = m1.sw_id.polissa_ref_id.id

                imd_obj = self.pool.get("ir.model.data")
                partner_obj = self.pool.get("res.partner")
                pol_obj = self.pool.get("giscedata.polissa")
                vat = partner_obj.read(cursor, uid, titular_id, ['vat'])['vat']
                if partner_obj.is_enterprise_vat(vat):
                    new_process = imd_obj.get_object_reference(
                        cursor, uid, "account_invoice_pending", "default_pending_state_process"
                    )[1]
                else:
                    new_process = imd_obj.get_object_reference(
                        cursor, uid, 'giscedata_facturacio_comer_bono_social',
                        'bono_social_pending_state_process'
                    )[1]
                pol_obj.write(cursor, uid, new_polissa_id, {
                              'process_id': new_process}, context=context)

        return res


GiscedataSwitchingM1_01()


class GiscedataSwitchingM1_05(osv.osv):
    """Classe per gestionar el canvi de comercialitzador"""

    _name = "giscedata.switching.m1.05"
    _inherit = "giscedata.switching.m1.05"

    def create(self, cursor, uid, values, context=None):
        res_id = super(GiscedataSwitchingM1_05, self).create(cursor, uid, values, context=context)
        # Forcem el recomput del camp function
        obj = self.browse(cursor, uid, res_id, context=context)
        if obj.dades_cau:
            self.pool.get('giscedata.switching')._store_set_values(
                cursor, uid, [obj.sw_id.id], ['collectiu_atr'], context)

        return res_id


GiscedataSwitchingM1_05()
