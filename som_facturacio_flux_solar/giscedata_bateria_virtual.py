# -*- encoding: utf-8 -*-
from osv import osv, fields
from datetime import datetime


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
            for origen_br in bateria_virtual.origen_ids:
                res[bateria_virtual.id] = str(origen_br.data_inici_descomptes)
        return res

    def _ff_data_app_descomptes(self, cursor, uid, bat_ids, name, args, context=None):
        res = dict.fromkeys(bat_ids, {'data_inici_app_descomptes': 0, 'data_final_app_descomptes': 0})
        sql = ("SELECT bat.id, bat_pol.data_inici, bat_pol.data_final "
               "FROM giscedata_bateria_virtual_polissa bat_pol "
               "JOIN giscedata_bateria_virtual bat ON bat.id = bat_pol.bateria_id "
               "WHERE bat.id in %(bat_ids)s")
        cursor.execute(sql, {'bat_ids': tuple(bat_ids)})
        aux = {x[0]: {'data_inici_app_descomptes': x[1], 'data_final_app_descomptes': x[2]} for x in cursor.fetchall()}
        res.update(aux)
        return res

    def _ff_bateria_activa(self, cursor, uid, bat_ids, name, args, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(bat_ids, False)
        avui = datetime.today().strftime("%Y-%m-%d")
        read_vals = ['data_inici_app_descomptes', 'data_final_app_descomptes']
        for bat_id in bat_ids:
            dates = self.read(cursor, uid, bat_id, read_vals, context=context)
            if (dates['data_inici_app_descomptes'] <= avui and
            (not dates['data_final_app_descomptes'] or dates['data_final_app_descomptes'] >= avui)):
                res[bat_id] = True
        return res

    _columns = {
        'origen_info': fields.function(_ff_origen, type="text", method=True, string='Origen'),
        'receptor_info': fields.function(_ff_receptor, type="text", method=True, string='Receptor (pes)'),
        'data_inici_descomptes': fields.function(_ff_data_inici_descomptes, type="text", method=True, string='Data inici generació descomptes'),
        'activa': fields.function(_ff_bateria_activa, type="boolean", method=True, string='Activa'),
        'data_inici_app_descomptes': fields.function(_ff_data_app_descomptes, type="text", method=True, string='Data inici aplicació descomptes', multi='data_app'),
        'data_final_app_descomptes': fields.function(_ff_data_app_descomptes, type="text", method=True, string='Data final aplicació descomptes', multi='data_app'),
    }


GiscedataBateriaVirtual()
