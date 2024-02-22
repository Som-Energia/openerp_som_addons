# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _


SELECTABLE_MODELS = [
    ("res.partner", _("Fitxa client")),
    ("res.partner.address", _("Adreça fitxa client")),
]

SELECTABLE_MODELS_LIST = [tup[0] for tup in SELECTABLE_MODELS]

SELECTABLE_TYPES_LIST = ['char', 'text']


class SomStash(osv.osv):
    _name = 'som.stash'

    def _get_selectable_models_list(self, cursor, uid, context=None):
        return SELECTABLE_MODELS_LIST

    _columns = {
        'origin': fields.reference(_('Origen'), selection=SELECTABLE_MODELS, size=128),
        'res_field': fields.char(_('Camp'), size=64),
        'res_id': fields.integer(_('ID')),
        'value': fields.text(_('Valor')),
        'date_stashed': fields.datetime(_('Data backup')),
    }

    _defaults = {
    }

    _sql_constraints = [
        ('origin_field_uniq', 'unique(origin, res_field)',
         'You cannot have an origin and field more than once'),
    ]


SomStash()
