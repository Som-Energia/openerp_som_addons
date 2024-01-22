# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomGurb(osv.osv):
    _name = "som.gurb"
    _description = _('Grup generació urbana')

    _columns = {
        'name': fields.char('Nom GURB', size=60, required=True),
        'code': fields.char('Codi GURB', size=60, required=True),
    }


SomGurb()
