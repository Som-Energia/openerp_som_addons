# -*- coding: utf-8 -*-
from osv import osv, fields

class GiscedataSwitchingWizardValidateD101(osv.osv_memory):
    _name = "wizard.validate.d101"
    _inherit = "wizard.validate.d101"

    _change_reason = ''

    def _get_change_reason(self, cursor, uid, ids):
        sw_obj = self.pool.get("giscedata.switching")
        wizard_vals = self.read(cursor, uid, ids)[0]
        sw_id =  wizard_vals['sw_id']
        sw = sw_obj.browse(cursor, uid, sw_id)

        pas_id = sw.step_ids[0].pas_id
        d101_obj = self.pool.get("giscedata.switching.d1.01")
        id_pas = int(pas_id.split(',')[1])
        self._change_reason = d101_obj.read(cursor, uid, id_pas, ['motiu_canvi'])['motiu_canvi']

    def mod_con_wizard_default_values(self, cursor, uid, ids, context=None):
        res = super(GiscedataSwitchingWizardValidateD101, self).mod_con_wizard_default_values(cursor, uid, ids, context)

        if self._change_reason == '06':
            values = {
                "generate_new_contract": 'exists',
                "change_adm": 1,
                "change_atr": 0,
                "owner_change_type": 'R'
            }
            res.update(values)
        return res
        
    def validate_d101_autoconsum(self, cursor, uid, ids, context=None):
        """
        Overwrite this method to manage 04 and 06 change reason 
        """
        self._get_change_reason(cursor, uid, ids) 

        res = super(GiscedataSwitchingWizardValidateD101, self).validate_d101_autoconsum(cursor, uid, ids, context)

        if res[1] and self._change_reason == '06':
            d102_obj = self.pool.get("giscedata.switching.d1.02")
            sw_id = d102_obj.read(cursor, uid, res[0], ['sw_id'])['sw_id'][0]
            sw_obj = self.pool.get('giscedata.switching')
            sw_obj.write(cursor, uid, sw_id, {"state": "done"})

        return res

GiscedataSwitchingWizardValidateD101()