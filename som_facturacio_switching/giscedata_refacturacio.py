# -*- coding: utf-8 -*-
from osv import osv


class GiscedataRefacturacio(osv.osv):
    _name = 'giscedata.refacturacio'
    _inherit = 'giscedata.refacturacio'


def create(self, cursor, uid, values, context=None):
    if context is None:
        context = {}

    res = super(GiscedataRefacturacio, self).create(cursor, uid, values, context=context)

    type_factura = self._get_tipo_origen(cursor, uid, res, context=context).get(res)

    if type_factura == 'G':
        self.write(cursor, uid, res, {'refacturat': True}, context=context)

    return res