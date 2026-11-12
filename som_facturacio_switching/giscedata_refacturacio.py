# -*- coding: utf-8 -*-
from osv import osv


class GiscedataRefacturacio(osv.osv):
    _name = "giscedata.refacturacio"
    _inherit = "giscedata.refacturacio"

    def create(self, cursor, uid, values, context=None):
        if context is None:
            context = {}

        res = super(GiscedataRefacturacio, self).create(cursor, uid, values, context=context)

        ref = self.read(cursor, uid, res, ["referencia"], context=context).get("referencia")

        if ref:
            ref_model = ref.split(",")[0]
            if ref_model == "giscedata.facturacio.importacio.linia":
                f1_o = self.pool.get(ref_model)
                f1_id = ref.split(",")[1].replace(" ", "")
                type_factura = f1_o.read(
                    cursor, uid, int(f1_id), ["type_factura"], context=context
                ).get("type_factura")

                if type_factura == "G":
                    self.write(cursor, uid, res, {"refacturat": True}, context=context)

        return res


GiscedataRefacturacio()
