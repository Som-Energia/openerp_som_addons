# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from osv.osv import TransactionExecute
import pooler
from psycopg2.errors import LockNotAvailable
from datetime import datetime
import logging
import time
from tools import float_round


class GiscedataBateriaVirtual(osv.osv):

    _name = "giscedata.bateria.virtual"
    _inherit = 'giscedata.bateria.virtual'

    def _ff_origen(self, cursor, uid, ids, name, args, context=None):
        res = {}
        for bateria_virtual in self.browse(cursor, uid, ids, context):
            if bateria_virtual.origen_ids:
                for origen_id in bateria_virtual.origen_ids:
                    res[origen_id] = str(origen_id.name)
        return res

    def _ff_receptor(self, cursor, uid, ids, name, args, context=None):
        res = {}
        for bateria_virtual in self.browse(cursor, uid, ids, context):
            if bateria_virtual.polissa_ids:
                for polissa_id in bateria_virtual.polissa_ids:
                    pes = ""
                    if bateria_virtual.polissa_ids.pes:
                        pes = str(bateria_virtual.polissa_ids.pes)
                    res[polissa_id] = str(polissa_id.name) + ", " + pes
        return res

    def _ff_data_inici_descomptes(self, cursor, uid, ids, name, args, context=None):
        res = {}
        for bateria_virtual in self.browse(cursor, uid, ids, context):
            if bateria_virtual.polissa_ids.data_final:
                res[bateria_virtual.id] = bateria_virtual.polissa_ids.data_final
        return res

    _columns = {
        'origen_id': fields.function(_ff_origen, type="text", method=True, string='Origen'),
        'receptor_info': fields.function(_ff_receptor, type="text", method=True, string='Receptor'),
        'data_inici_descomptes': fields.function(_ff_data_inici_descomptes, type="text", method=True, string='Receptor'),
    }


GiscedataBateriaVirtual()

