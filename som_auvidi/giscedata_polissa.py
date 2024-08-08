# coding=utf-8
from __future__ import absolute_import
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    _columns = {
        'te_auvidi': fields.boolean(
            'Té AUVIDI',
            readonly=True,
            states={
                'esborrany': [('readonly', False)],
                'validar': [('readonly', False)],
                'modcontractual': [('readonly', False)]
            }),
    }


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    _columns = {
        'te_auvidi': fields.boolean('Té AUVIDI')
    }


GiscedataPolissaModcontractual()
