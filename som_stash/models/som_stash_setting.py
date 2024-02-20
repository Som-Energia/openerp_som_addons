# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from som_stash import SELECTABLE_MODELS_LIST, SELECTABLE_TYPES_LIST


class SomStashSetting(osv.osv):
    _name = 'som.stash.setting'

    def _ff_get_allowed(self, cursor, uid, ids, name, args, context=None):
        res = {}
        for val in self.browse(cursor, uid, ids, context=context):
            res[val.id] = {
                'allowed_models': SELECTABLE_MODELS_LIST,
                'allowed_types': SELECTABLE_TYPES_LIST,
            }
        return res

    _columns = {
        'allowed_models': fields.function(
            _ff_get_allowed, type="char", method=True, string="Allowed models", multi=True
        ),
        'allowed_types': fields.function(
            _ff_get_allowed, type="char", method=True, string="Allowed types", multi=True
        ),
        'model': fields.many2one('ir.model', 'Model'),
        'field': fields.many2one('ir.model.fields', 'Camp'),
        'default_stashed_value': fields.text(_('Valor per defecte')),
    }

    _defaults = {
    }

    _sql_constraints = [
        ('model_field_uniq', 'unique(model,field)',
         'You cannot have one field configured more than once'),
    ]


SomStashSetting()
