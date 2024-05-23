# -*- coding: utf-8 -*-
from osv import osv, fields


class AgrupacioSupramunicipal(osv.osv):
    _name = 'agrupacio.supramunicipal'
    _description = '''AAPP que gestionen les consultes de pobresa energètica'''

    _columns = {
        'name': fields.char("Nom", size=128),
        'active': fields.boolean(
            string=(u"Actiu"), help=(u"Indica si fem consultes a aquesta agrupació")
        ),
    }
    _order = "id desc"


AgrupacioSupramunicipal()
