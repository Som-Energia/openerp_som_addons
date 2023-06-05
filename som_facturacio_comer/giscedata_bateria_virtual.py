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
        for bateria_virtual in self.browse(cursor, uid, ids, context={'prefetch': False}):
            origens = ""
            for it, origen_br in enumerate(bateria_virtual.origen_ids):
                # A partir d'ara nomes n'hi haura un pero en antigues bateries pot ser que no
                model, id = origen_br.origen_ref.split(",")
                model_obj = self.pool.get(model)
                name = model_obj.read(cursor, uid, int(id), ['name'])['name']
                if it > 0:
                    origens += "\n" + str(name)
                else:
                    origens += str(name)
            res[bateria_virtual.id] = origens
        return res

    def _ff_receptor(self, cursor, uid, ids, name, args, context=None):
        res = {}
        for bateria_virtual in self.browse(cursor, uid, ids, context={'prefetch': False}):
            receptors = ""
            for it, polissa_br in enumerate(bateria_virtual.polissa_ids):
                # A partir d'ara nomes n'hi haura un pero en antigues bateries pot ser que no
                name = polissa_br.polissa_id.name
                pes = polissa_br.pes
                msg = str(name) + " (" + str(pes) + ")"
                if it > 0:
                    receptors += "\n" + msg
                else:
                    receptors += msg
            res[bateria_virtual.id] = receptors
        return res

    def _ff_data_inici_descomptes(self, cursor, uid, ids, name, args, context=None):
        res = {}
        for bateria_virtual in self.browse(cursor, uid, ids, context={'prefetch': False}):
            for polissa_br in bateria_virtual.polissa_ids:
                res[bateria_virtual.id] = str(polissa_br.data_inici)
        return res

    _columns = {
        'origen_info': fields.function(_ff_origen, type="text", method=True, string='Origen'),
        'receptor_info': fields.function(_ff_receptor, type="text", method=True, string='Receptor (pes)'),
        'data_inici_descomptes': fields.function(_ff_data_inici_descomptes, type="text", method=True, string='Data inici descomptes'),
    }


GiscedataBateriaVirtual()

