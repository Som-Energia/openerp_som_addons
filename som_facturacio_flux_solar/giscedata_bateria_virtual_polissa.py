# -*- coding: utf-8 -*-

from datetime import datetime

from osv import osv, fields
from tools.translate import _


class GiscedataBateriaVirtualPolissa(osv.osv):
    _name = "giscedata.bateria.virtual.polissa"
    _inherit = 'giscedata.bateria.virtual.polissa'
    
    def create(self, cursor, uid, vals, context=None):
        percentatge_acum_obj = self.pool.get('giscedata.bateria.virtual.percentatges.acumulacio')
        origen_obj = self.pool.get('giscedata.bateria.virtual.origen')
        conf_obj = self.pool.get('res.config')

        bat_polissa_id = super(GiscedataBateriaVirtualPolissa, self).create(cursor, uid, vals, context=context)
        polissa_br = self.browse(cursor, uid, bat_polissa_id, context={'prefetch': False})

        percentatge_defecte = int(conf_obj.get(cursor, uid, 'percentatge_acumulacio', '100'))

        origen_ids = polissa_br.bateria_id.origen_ids
        for origen_id in origen_ids:
            percentatge_acum_obj.create(cursor, uid, {
                'percentatge': percentatge_defecte,
                'data_inici': polissa_br.data_inici,
                'data_fi': None,
                'origen_id': origen_id.id,
            })


GiscedataBateriaVirtualPolissa()
