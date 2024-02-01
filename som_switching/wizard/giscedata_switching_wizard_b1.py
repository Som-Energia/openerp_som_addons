# -*- coding: utf-8 -*-
from osv import osv, fields, orm


class GiscedataSwitchingWizardB101(osv.osv_memory):
    """Wizard pel switching"""

    _name = "giscedata.switching.b101.wizard"
    _inherit = "giscedata.switching.b101.wizard"

    def get_config_vals(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        wizard = self.browse(cursor, uid, ids[0], context)

        config_vals = super(GiscedataSwitchingWizardB101, self).get_config_vals(
            cursor, uid, ids, context
        )
        config_vals["phone_pre"] = wizard.phone_pre
        config_vals["phone_num"] = wizard.phone_num
        return config_vals

    _columns = {
        "phone_num": fields.char("Telèfon", size=9),
        "phone_pre": fields.char("Prefix", size=2),
    }

    _defaults = {
        "phone_pre": "34",
    }


GiscedataSwitchingWizardB101()
