# -*- coding: utf-8 -*-
from osv import osv


class ResMunicipi(osv.osv):
    _name = 'res.municipi'
    _inherit = 'res.municipi'

    def filter_compatible_pricelists(self, cursor, uid, municipi_id,
                                     pricelist_list, context=None):
        if isinstance(municipi_id, (tuple, list)):
            municipi_id = municipi_id[0]

        sufix = '_SOM'

        municipi = self.browse(cursor, uid, municipi_id, context=context)

        # test electric subsystem
        if municipi.subsistema_id.code != 'PE':
            sufix = '_SOM_INSULAR'

        filtered_list = [p for p in pricelist_list if p.name.endswith(sufix) > 0]

        return filtered_list

ResMunicipi()