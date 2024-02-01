# -*- coding: utf-8 -*-
from datetime import datetime
from osv import osv, fields
from tools.translate import _


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def get_auto_bat_name(self, cursor, uid, polissa_id, polissa_name, context=None):
        if context is None:
            context = {}
        return "FS" + str(polissa_name)

    def is_autoconsum_amb_excedents(self, cursor, uid, autoconsumo, context=None):
        if context is None:
            context = {}
        if autoconsumo in ("41", "42", "43"):
            return True
        else:
            return False

    def get_bateria_virtual_data_inici_for_invoice(self, cursor, uid, factura, context=None):
        if context is None:
            context = {}
        bat_polissa_obj = self.pool.get("giscedata.bateria.virtual.origen")
        origen_ref = "giscedata.polissa,{}".format(factura.polissa_id.id)
        dates_inici = (
            bat_polissa_obj.q(cursor, uid)
            .read(["data_inici_descomptes"])
            .where([("origen_ref", "=", origen_ref)])
        )
        if dates_inici:
            data_inici_bateria = max([d["data_inici_descomptes"] for d in dates_inici])
        else:
            data_inici_bateria = False
        return data_inici_bateria


GiscedataPolissa()
